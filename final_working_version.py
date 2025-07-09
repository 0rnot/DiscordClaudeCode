#!/usr/bin/env python3
"""
Fixed implementation that properly handles MCP server and Discord bot integration
Based on Rust implementation analysis
"""
import asyncio
import json
import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

# Google AI SDK for title generation
try:
    import google.generativeai as genai
except ImportError:
    genai = None
    logging.warning("Google AI SDK not available - title generation will use fallback method")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Global state
pending_questions = {}
discord_client = None

class HumanInDiscord:
    """Discord-based human interaction handler"""
    
    def __init__(self, client, channel_id: int, user_id: int):
        self.client = client
        self.channel_id = channel_id
        self.user_id = user_id
        self.thread_id = None  # Persistent thread like Rust OnceCell
        self.thread_title = None
        self.is_forum = None  # Cache for channel type
        self.conversation_count = 0  # Track conversation exchanges
        self.conversation_history = []  # Store conversation for title generation
    
    def create_thread_name(self, question: str) -> str:
        """Create a valid Discord thread name (1-100 characters)"""
        if not question.strip():
            return "AI Assistant Question"
        
        first_line = question.strip().split('\n')[0]
        
        # 疑問符や感嘆符で文を分割
        sentences = []
        for delimiter in ['.', '!', '?']:
            if delimiter in first_line:
                sentences = [s.strip() for s in first_line.split(delimiter) if s.strip()]
                break
        
        if not sentences:
            sentences = [first_line]
        
        # 疑問文があれば優先的に使用
        title = None
        for sentence in sentences:
            if '?' in sentence:
                title = sentence.strip()
                break
        
        if not title:
            title = sentences[0].strip()
        
        # 空文字列チェック
        if not title:
            title = "AI Assistant Question"
        
        # 100文字制限に対応
        if len(title) > 100:
            title = title[:100]
        
        # 最終的な長さチェック（1-100文字）
        if len(title) < 1 or len(title) > 100:
            title = "AI Assistant Question"
            
        return title
    
    async def analyze_conversation_for_title(self) -> str:
        """Analyze conversation history to generate a better title using Gemini AI"""
        if len(self.conversation_history) < 6:  # Need at least 3 exchanges (6 messages)
            return None
            
        # Get latest 6 messages for analysis
        recent_messages = self.conversation_history[-6:]
        conversation_text = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(recent_messages)])
        
        # Try AI-powered title generation first
        ai_title = await self._generate_ai_title(conversation_text)
        if ai_title:
            return ai_title
            
        # Fallback to simple keyword extraction
        return self._fallback_title_generation(recent_messages)
    
    async def _generate_ai_title(self, conversation_text: str) -> Optional[str]:
        """Generate title using Gemini 2.0 Flash API"""
        if not genai:
            logging.warning("Google AI SDK not available for title generation")
            return None
            
        try:
            # Get API key from environment
            api_key = os.getenv('GOOGLE_AI_API_KEY')
            if not api_key:
                logging.warning("GOOGLE_AI_API_KEY not found in environment variables")
                return None
                
            # Initialize Gemini client
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Prepare prompt for title generation
            prompt = f"""以下の会話から短くて分かりやすいタイトルを作成してください。

制約:
- 必ず30文字以内にする
- 技術用語はそのまま使用
- タイトルのみ回答（説明や前置きは不要）
- 日本語で簡潔に

会話履歴:
{conversation_text}

回答例: Python Discord Bot開発"""
            
            # Generate title using Gemini 2.0 Flash
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
            
            if response and response.text:
                title = response.text.strip()
                # Ensure title length is within Discord limits
                if len(title) > 100:
                    title = title[:100]
                logging.info(f"🤖 AI-generated title: {title}")
                return title
                
        except Exception as e:
            logging.error(f"❌ Failed to generate AI title: {e}")
            
        return None
    
    def _fallback_title_generation(self, messages: list) -> Optional[str]:
        """Fallback title generation using simple keyword extraction"""
        all_text = " ".join(messages)
        
        # Simple keyword extraction
        tech_keywords = ['python', 'discord', 'error', 'bug', 'api', 'code', 'function', '問題', 'エラー']
        action_keywords = ['作成', 'create', '修正', 'fix', '実装', 'implement', '解決', 'solve']
        
        found_tech = [kw for kw in tech_keywords if kw.lower() in all_text.lower()]
        found_action = [kw for kw in action_keywords if kw.lower() in all_text.lower()]
        
        if found_tech and found_action:
            title = f"{found_action[0]} {found_tech[0]}"
            if len(title) > 100:
                title = title[:100]
            return title
        elif found_tech:
            return f"{found_tech[0]}について"
        elif '?' in all_text or '？' in all_text:
            # Extract first question
            for msg in messages[:3]:
                if '?' in msg or '？' in msg:
                    sentences = msg.split('。')
                    for sentence in sentences:
                        if '?' in sentence or '？' in sentence:
                            clean_sentence = sentence.strip().replace('\n', ' ')
                            if len(clean_sentence) > 100:
                                clean_sentence = clean_sentence[:100]
                            return clean_sentence
        
        return "AI Assistant Question"  # Final fallback

    async def get_or_create_thread(self, question: str):
        """Get existing thread or create new one (mimics Rust OnceCell behavior)"""
        # Try to reuse existing thread
        if self.thread_id:
            try:
                thread = self.client.get_channel(self.thread_id)
                if thread and hasattr(thread, 'archived') and not thread.archived:
                    self._thread_reused = True
                    return thread, self.is_forum
            except:
                pass
        
        # Create new thread (first question or thread no longer accessible)
        channel = self.client.get_channel(self.channel_id)
        if not channel:
            raise Exception(f"Channel {self.channel_id} not found")
        
        # チャンネルタイプを確認
        is_forum = isinstance(channel, discord.ForumChannel)
        self.is_forum = is_forum
        
        thread_name = self.create_thread_name(question)
        
        if is_forum:
            # フォーラムチャンネルの場合
            thread_result = await channel.create_thread(
                name=thread_name,
                content=question,  # 必須パラメータ
                auto_archive_duration=1440
            )
            thread = thread_result.thread
        else:
            # 通常のテキストチャンネルの場合
            thread = await channel.create_thread(
                name=thread_name,
                message=None,
                auto_archive_duration=1440
            )
        
        self.thread_id = thread.id
        self.thread_title = thread_name
        self._thread_reused = False
        return thread, is_forum

    async def report_message(self, message: str, timeout: int = 3) -> None:
        """Report a message to human without waiting for response"""
        try:
            # Get user
            user = self.client.get_user(self.user_id)
            if not user:
                try:
                    user = await self.client.fetch_user(self.user_id)
                except:
                    logging.error(f"Error: User {self.user_id} not found")
                    return
            
            # Add message to conversation history (for title updates)
            self.conversation_history.append(message)
            self.conversation_count += 1
            
            # Get or create persistent thread (reuse existing logic)
            thread, is_forum = await self.get_or_create_thread(message)
            
            # Send message to Discord
            if hasattr(self, '_thread_reused') and self._thread_reused:
                await thread.send(f"{message}")
            elif not is_forum:
                await thread.send(f"{message}")
            
            # Wait for specified timeout (do not wait for response)
            await asyncio.sleep(timeout)
            
            # Check if we should update the title
            if self.conversation_count == 6 or (self.conversation_count > 6 and self.conversation_count % 10 == 0):
                await self.update_thread_title_if_needed(thread)
            
            logging.info(f"🔔 Message reported and timeout completed")
            
        except Exception as e:
            logging.error(f"❌ Error in report_message: {e}")
            raise
    
    async def ask(self, question: str) -> str:
        """Ask a question to human via Discord and wait for response"""
        try:
            # Get user
            user = self.client.get_user(self.user_id)
            if not user:
                try:
                    user = await self.client.fetch_user(self.user_id)
                except:
                    return f"Error: User {self.user_id} not found"
            
            # Add question to conversation history
            self.conversation_history.append(question)
            self.conversation_count += 1
            
            # Get or create persistent thread
            thread, is_forum = await self.get_or_create_thread(question)
            
            # 既存スレッドを再利用している場合は、新しい質問を送信
            if hasattr(self, '_thread_reused') and self._thread_reused:
                await thread.send(f"{question}")
            # フォーラムチャンネルでない場合は、質問メッセージを送信
            # （フォーラムの場合は作成時に既に送信済み）
            elif not is_forum:
                await thread.send(f"{question}")
            
            # Wait for response
            future = asyncio.Future()
            pending_questions[thread.id] = future
            
            try:
                response = await asyncio.wait_for(future, timeout=21600)
                
                # Add response to conversation history
                self.conversation_history.append(response)
                self.conversation_count += 1
                
                # Check if we should update the title (after 3 exchanges = 6 messages)
                if self.conversation_count == 6 or (self.conversation_count > 6 and self.conversation_count % 10 == 0):  # Check at 6, then every 10 messages
                    await self.update_thread_title_if_needed(thread)
                
                return response
            except asyncio.TimeoutError:
                pending_questions.pop(thread.id, None)
                return "No response received within 6 hours"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def update_thread_title_if_needed(self, thread):
        """Update thread title based on conversation analysis"""
        try:
            new_title = await self.analyze_conversation_for_title()
            if new_title and new_title != self.thread_title:
                logging.info(f"🏷️ Updating thread title: '{self.thread_title}' -> '{new_title}'")
                await thread.edit(name=new_title)
                self.thread_title = new_title
                logging.info(f"✅ Thread title updated successfully")
        except Exception as e:
            logging.error(f"❌ Failed to update thread title: {e}")

class HumanInTheLoopBot(commands.Bot):
    """Discord bot for human-in-the-loop interactions"""
    
    def __init__(self, channel_id: int, user_id: int):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.target_channel_id = channel_id
        self.target_user_id = user_id
        
    async def on_ready(self):
        logging.info(f'Discord bot ready! Logged in as {self.user}')
        
    async def on_message(self, message):
        if message.author == self.user:
            return
            
        if (isinstance(message.channel, discord.Thread) and 
            message.channel.parent_id == self.target_channel_id and 
            message.author.id == self.target_user_id):
            
            thread_id = message.channel.id
            if thread_id in pending_questions:
                future = pending_questions.pop(thread_id)
                if not future.done():
                    future.set_result(message.content)

class MCPHandler:
    """MCP request handler"""
    
    def __init__(self, human_handler: HumanInDiscord):
        self.human_handler = human_handler
    
    async def handle_request(self, request):
        """Handle MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": True}},
                    "serverInfo": {"name": "human-in-the-loop", "version": "1.0.0"}
                }
            }
        
        elif method == "notifications/initialized":
            return None
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [{
                        "name": "ask_human",
                        "description": "Ask a human for information that only they would know",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"question": {"type": "string", "description": "The question to ask the human"}},
                            "required": ["question"]
                        }
                    }, {
                        "name": "report_to_human",
                        "description": "Report a message to human without waiting for response",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "Message to report"},
                                "timeout": {"type": "number", "description": "Timeout in seconds (default: 3)"}
                            },
                            "required": ["message"]
                        }
                    }]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "ask_human":
                question = arguments.get("question", "")
                logging.info(f"🔧 ask_human called with: {question[:50]}...")
                
                try:
                    response_text = await self.human_handler.ask(question)
                    logging.info(f"✅ Got response: {response_text[:50]}...")
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": response_text}]
                        }
                    }
                except Exception as e:
                    logging.error(f"❌ Error in ask_human: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
            
            elif tool_name == "report_to_human":
                message = arguments.get("message", "")
                timeout = arguments.get("timeout", 3)
                logging.info(f"🔧 report_to_human called with: {message[:50]}...")
                
                try:
                    await self.human_handler.report_message(message, timeout)
                    logging.info(f"✅ Message reported successfully")
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [{"type": "text", "text": "Message reported successfully"}]
                        }
                    }
                except Exception as e:
                    logging.error(f"❌ Error in report_to_human: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }

async def handle_stdin_input(mcp_handler):
    """Handle stdin input asynchronously"""
    loop = asyncio.get_event_loop()
    
    while True:
        try:
            # Read line from stdin asynchronously
            line = await loop.run_in_executor(None, sys.stdin.readline)
            
            if not line:  # EOF
                logging.info("📪 EOF received")
                break
                
            line = line.strip()
            if not line:
                continue
            
            logging.info(f"📨 Received: {line[:100]}...")
            request = json.loads(line)
            response = await mcp_handler.handle_request(request)
            
            if response:
                print(json.dumps(response), flush=True)
                logging.info(f"📤 Sent response")
                
        except json.JSONDecodeError as e:
            logging.error(f"❌ Invalid JSON: {e}")
        except Exception as e:
            logging.error(f"❌ Error processing request: {e}")

async def main():
    """Main function - properly integrated like Rust tokio::select!"""
    parser = argparse.ArgumentParser(description="Human-in-the-loop MCP server")
    parser.add_argument("--discord-channel-id", type=int, required=True)
    parser.add_argument("--discord-user-id", type=int, required=True)
    
    args = parser.parse_args()
    
    # Get Discord token
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        logging.error("❌ DISCORD_TOKEN environment variable is required")
        sys.exit(1)
    
    logging.info(f"🎯 Starting with channel_id={args.discord_channel_id}, user_id={args.discord_user_id}")
    
    # Create Discord bot
    bot = HumanInTheLoopBot(args.discord_channel_id, args.discord_user_id)
    
    # Create human handler
    human_handler = HumanInDiscord(bot, args.discord_channel_id, args.discord_user_id)
    
    # Create MCP handler
    mcp_handler = MCPHandler(human_handler)
    
    # Store bot globally for access
    global discord_client
    discord_client = bot
    
    # Run both Discord bot and stdin handler concurrently
    # This mimics Rust's tokio::select! behavior
    try:
        logging.info("🚀 Starting Discord bot and MCP stdin handler")
        await asyncio.gather(
            bot.start(discord_token),
            handle_stdin_input(mcp_handler)
        )
    except KeyboardInterrupt:
        logging.info("🛑 Shutting down...")
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())