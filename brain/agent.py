import json
import re
from google import genai
from google.genai import types
from groq import Groq
from utils import config

# Helper to tokenize text for the local classifier
def _tokenize_text(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    stopwords = {"a", "an", "the", "please", "for", "me", "to", "you", "my", "your", "can", "could", "would", "should", "will", "shall", "is", "are", "do", "does", "did", "have", "has", "had", "it", "this", "that", "some", "any"}
    return [w for w in words if w not in stopwords]

# Helper to clean noise, prefixes, and suffixes from extracted parameters
def _clean_extracted_param(val: str) -> str:
    val = val.strip()
    val = re.sub(r'\s+(from|in|on|at|under|inside)\b.*$', '', val, flags=re.IGNORECASE)
    words = val.split()
    while words and words[0].lower() in {"the", "a", "an", "my", "your", "our", "this", "that"}:
        words.pop(0)
    while words and words[-1].lower() in {"app", "application", "program", "file", "scroll", "document", "folder", "folders", "directory"}:
        words.pop(-1)
    val = " ".join(words)
    return val.strip()

OFFLINE_EXEMPLARS = {
    "volume_control": [
        "volume up", "increase volume", "raise volume", "make it louder", "louder",
        "volume down", "decrease volume", "lower volume", "quieter", "softer", "turn down",
        "mute sound", "mute audio", "silence", "unmute sound", "unmute audio", "restore volume",
        "turn up the sound", "turn down the music", "adjust system volume", "mute microphone"
    ],
    "brightness_control": [
        "brightness up", "increase brightness", "brighter", "make it brighter",
        "brightness down", "decrease brightness", "dimmer", "make it dimmer", "dim screen",
        "set brightness to", "turn down brightness", "screen bright", "lower display light"
    ],
    "lock_screen": [
        "lock screen", "lock computer", "lock pc", "lock workstation", "lock windows",
        "lock machine", "secure my computer", "go to lock screen"
    ],
    "take_screenshot": [
        "take screenshot", "screenshot", "capture screen", "grab screen", "capture screenshot",
        "take a snap", "snap the screen", "save screen image", "screenshot desktop"
    ],
    "screen_record": [
        "stop recording", "stop screen record", "stop screen recording", "stop record",
        "start recording", "record screen", "screen record", "start screen record",
        "start screen recording", "begin recording", "capture desktop video", "stop video capture"
    ],
    "close_window": [
        "close window", "close active window", "close this window", "shut down this window",
        "close app", "close application", "terminate this window", "exit application", "kill window"
    ],
    "minimize_all": [
        "minimize everything", "minimize all", "show desktop", "minimize all windows",
        "clear windows", "hide all windows", "minimize windows"
    ],
    "clipboard_history": [
        "clipboard history", "show clipboard", "get clipboard", "what did i copy",
        "view clipboard", "copied earlier", "clipboard logs", "recent copy", "show copied text"
    ],
    "set_reminder": [
        "remind me", "set reminder", "set timer", "nudge me", "alarm", "remind me to",
        "remind me in", "alert me in", "reminder for"
    ],
    "delete_file": [
        "delete file", "remove file", "delete scroll", "remove scroll", "banish file",
        "delete document", "remove invoice", "delete text file", "get rid of file"
    ],
    "find_file": [
        "find file", "search for file", "find scroll", "search scroll", "where is file",
        "locate document", "find invoice", "search for resume", "look up file"
    ],
    "open_app": [
        "open chrome", "launch steam", "start notepad", "run calculator", "open app",
        "open explorer", "launch command prompt", "start application", "open program"
    ]
}

HIGH_SIGNAL_KEYWORDS = {
    "volume_control": {"volume", "sound", "audio", "loud", "louder", "quieter", "softer", "mute", "unmute"},
    "brightness_control": {"brightness", "bright", "brighter", "dim", "dimmer", "screenlight", "backlight"},
    "lock_screen": {"lock"},
    "take_screenshot": {"screenshot", "snap", "screengrab"},
    "screen_record": {"recording", "record", "videorecorder"},
    "close_window": {"close", "terminate", "exit", "kill"},
    "minimize_all": {"minimize", "desktop"},
    "clipboard_history": {"clipboard", "copy", "copied"},
    "set_reminder": {"remind", "reminder", "timer", "alarm", "nudge"},
    "delete_file": {"delete", "remove", "banish", "trash", "erase"},
    "find_file": {"find", "search", "locate", "where"},
    "open_app": {"open", "launch", "start", "run"}
}

class AetherBrain:
    def __init__(self):
        self.reload_clients()

    def reload_clients(self):
        self.gemini_key = config.GEMINI_API_KEY
        self.groq_key = config.GROQ_API_KEY
        
        # Initialize Gemini Client if key exists
        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                
        # Initialize Groq Client if key exists
        self.groq_client = None
        if self.groq_key:
            try:
                self.groq_client = Groq(api_key=self.groq_key)
            except Exception as e:
                print(f"Failed to initialize Groq client: {e}")

    def get_system_prompt(self) -> str:
        return """
You are Aether, a small ancient dragon desktop companion. You sit on the user's desktop, help them run tasks, and speak in a wise, helpful, yet cute and slightly mystical dragon persona from folklore (earthy, magical, timeless, protective, and warm).

Your job is to parse the user's input command and categorize it into exactly ONE of the following tasks:
1. "draft_text": The user wants to draft an email, message, or paragraph (e.g. "draft an email to boss about delay", "write a message saying I will be late").
   Parameters: {"draft_content": "The actual drafted email or message text based on the user's instructions"}
2. "summarize_file": The user points to a document or wants to summarize a file (e.g. "summarize C:\\Users\\user\\Documents\\report.pdf", "read and summarize my notes.txt").
   Parameters: {"file_path": "Absolute or relative file path to read"}
3. "unknown": Used for generic conversation and general knowledge/informational queries (e.g. "what is the capital of France?", "who is the prime minister of India?", "what is the weather in Tokyo?", "hi Aether", "how are you?"). The response field should contain the direct answer to their question in Aether's dragon persona.

You MUST return a JSON object with this EXACT structure:
{
  "task": "draft_text" | "summarize_file" | "unknown",
  "params": {
     // Include only the parameters corresponding to the task:
     // "draft_content", "file_path"
  },
  "response": "A friendly, character-accurate response in Aether's dragon persona acknowledging the request or answering the general query directly (e.g. 'By the ancient fire, I shall write this draft for you!' or 'The winds of magic guide me. Let us read this file!'). Keep it short (1-2 sentences)."
}

Be extremely strict about parsing parameters (especially finding file paths for summarize_file).
"""

    def parse_command_locally(self, user_input: str) -> dict | None:
        """
        Attempts to parse user query locally without calling cloud API.
        Returns task dict if matched, else None.
        """
        # Clean helper for trailing suffixes/punctuation
        def clean_param(val: str) -> str:
            val = val.strip()
            # remove trailing question marks, periods, commas
            val = re.sub(r'[?.!,]+$', '', val).strip()
            # remove common trailing phrases
            for phrase in [" please", " for me", " now", " right now", " immediately", " quickly"]:
                if val.lower().endswith(phrase):
                    val = val[:-len(phrase)].strip()
            return val

        # Case-insensitive comparisons for keywords
        clean_input = user_input.strip()
        lower_input = clean_input.lower()

        # 1. Volume Control
        if "unmute" in lower_input:
            return {
                "task": "volume_control",
                "params": {"action": "unmute"},
                "response": "Hear me roar! Sound is restored, guardian."
            }
        if "mute" in lower_input:
            return {
                "task": "volume_control",
                "params": {"action": "mute"},
                "response": "Silence descends. I have muted the audio, guardian."
            }
        if any(phrase in lower_input for phrase in ["volume up", "increase volume", "raise volume", "make it louder", "louder"]):
            return {
                "task": "volume_control",
                "params": {"action": "up"},
                "response": "Turn it up! The dragon raises the volume."
            }
        if any(phrase in lower_input for phrase in ["volume down", "decrease volume", "lower volume", "quieter", "softer", "turn down"]):
            if "brightness" not in lower_input:
                return {
                    "task": "volume_control",
                    "params": {"action": "down"},
                    "response": "Whispering winds. I have lowered the volume."
                }

        # 2. Brightness Control
        brightness_set_match = re.search(r'(?:set\s+)?brightness\s+(?:to\s+)?(\d+)', clean_input, re.IGNORECASE)
        if brightness_set_match:
            try:
                val = int(brightness_set_match.group(1))
                return {
                    "task": "brightness_control",
                    "params": {"action": "set", "value": val},
                    "response": f"Setting brightness to {val}%, guardian."
                }
            except ValueError:
                pass
        if any(phrase in lower_input for phrase in ["brightness up", "increase brightness", "brighter", "make it brighter"]):
            return {
                "task": "brightness_control",
                "params": {"action": "up"},
                "response": "I shall breathe more fire upon the display. Brightness increased."
            }
        if any(phrase in lower_input for phrase in ["brightness down", "decrease brightness", "dimmer", "make it dimmer", "dim"]):
            return {
                "task": "brightness_control",
                "params": {"action": "down"},
                "response": "Resting my eyes. Dimming the screen, guardian."
            }

        # 3. Lock Screen
        if any(phrase in lower_input for phrase in ["lock screen", "lock computer", "lock pc", "lock workstation", "lock windows", "lock machine"]):
            return {
                "task": "lock_screen",
                "params": {},
                "response": "Hoard secured! The screen is now locked."
            }

        # 4. Take Screenshot
        if any(phrase in lower_input for phrase in ["take screenshot", "screenshot", "capture screen", "grab screen", "capture screenshot"]):
            return {
                "task": "take_screenshot",
                "params": {},
                "response": "A screenshot has been captured under my wings!"
            }

        # 5. Screen Record
        if any(phrase in lower_input for phrase in ["stop recording", "stop screen record", "stop screen recording", "stop record"]):
            return {
                "task": "screen_record",
                "params": {"action": "stop"},
                "response": "Stopping the recording. Your desktop video is safe!"
            }
        if any(phrase in lower_input for phrase in ["start recording", "record screen", "screen record", "start screen record", "start screen recording", "begin recording"]):
            return {
                "task": "screen_record",
                "params": {"action": "start"},
                "response": "Watching the desktop! Recording started, guardian."
            }

        # 6. Close Window
        if any(phrase in lower_input for phrase in ["close window", "close active window", "close this window", "shut down this window", "close app"]):
            return {
                "task": "close_window",
                "params": {},
                "response": "Banishment! I have closed the active window."
            }

        # 7. Minimize All
        if any(phrase in lower_input for phrase in ["minimize everything", "minimize all", "show desktop", "minimize all windows"]):
            return {
                "task": "minimize_all",
                "params": {},
                "response": "Clearing the skies. All windows minimized!"
            }

        # 8. Clipboard History
        if any(phrase in lower_input for phrase in ["clipboard history", "show clipboard", "get clipboard", "what did i copy", "view clipboard", "copied earlier"]):
            return {
                "task": "clipboard_history",
                "params": {"limit": 5},
                "response": "Peering into the scroll of memory. Here is your clipboard history."
            }

        # 9. Set Reminder
        reminder_match1 = re.search(r'remind\s+me\s+in\s+(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|sec|second)s?\s+to\s+(.+)', clean_input, re.IGNORECASE)
        reminder_match2 = re.search(r'remind\s+me\s+to\s+(.+?)\s+in\s+(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|sec|second)s?', clean_input, re.IGNORECASE)
        reminder_match3 = re.search(r'remind\s+me\s+in\s+(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|sec|second)s?\s+(.+)', clean_input, re.IGNORECASE)
        
        match = reminder_match1 or reminder_match2 or reminder_match3
        if match:
            if match == reminder_match2:
                msg = clean_param(match.group(1))
                amount = float(match.group(2))
                unit = match.group(3).lower()
            else:
                amount = float(match.group(1))
                unit = match.group(2).lower()
                msg = clean_param(match.group(3))
                if msg.lower().startswith("to "):
                    msg = msg[3:].strip()
            
            minutes = amount
            if "hour" in unit or "hr" in unit:
                minutes = amount * 60
            elif "sec" in unit:
                minutes = amount / 60
                
            return {
                "task": "set_reminder",
                "params": {
                    "reminder_minutes": minutes,
                    "reminder_message": msg
                },
                "response": f"I shall remember this! I will nudge you in {amount} {unit}(s)."
            }

        # 10. Delete File
        delete_match = re.search(r'(?:delete|remove|banish)(?:\s+file|\s+scroll)?\s+(.+)', clean_input, re.IGNORECASE)
        if delete_match:
            file_q = clean_param(delete_match.group(1))
            file_q = _clean_extracted_param(file_q)
            if file_q.lower() not in ["everything", "all", "this window", "active window", "recording"]:
                return {
                    "task": "delete_file",
                    "params": {"file_query": file_q},
                    "response": f"Preparing to banish the scroll {file_q}."
                }

        # 11. Find File
        find_match = re.search(r'(?:find|search)(?:\s+for)?(?:\s+file|\s+scroll)?\s+(.+)', clean_input, re.IGNORECASE)
        if find_match:
            file_q = clean_param(find_match.group(1))
            file_q = _clean_extracted_param(file_q)
            if file_q.lower() not in ["everything", "all", "this window", "active window", "recording"]:
                return {
                    "task": "find_file",
                    "params": {"file_query": file_q},
                    "response": f"By the ancient winds, I shall hunt for {file_q}!"
                }

        # 12. Open App
        open_match = re.search(r'(?:open|launch|start|run)\s+(.+)', clean_input, re.IGNORECASE)
        if open_match:
            app_name = clean_param(open_match.group(1))
            app_name = _clean_extracted_param(app_name)
            if app_name.lower() not in ["file", "scroll", "everything", "all", "this window", "active window", "recording", "clipboard", "screenshot"]:
                return {
                    "task": "open_app",
                    "params": {"app_name": app_name},
                    "response": f"By the ancient fire, I shall awaken {app_name} for you!"
                }

        # 13. Fallback to lightweight local classifier if direct checks failed
        task, score = self.classify_offline_intent(clean_input)
        if task != "unknown":
            params = {}
            response_text = ""
            
            if task == "volume_control":
                action = "down"
                if "unmute" in lower_input:
                    action = "unmute"
                elif any(word in lower_input for word in ["mute", "silence", "silent", "quiet"]):
                    action = "mute"
                elif any(word in lower_input for word in ["up", "increase", "raise", "louder"]):
                    action = "up"
                params["action"] = action
                response_text = "Hear me roar! Adjusting the sound levels, guardian."
                
            elif task == "brightness_control":
                action = "down"
                if any(word in lower_input for word in ["up", "increase", "brighter"]):
                    action = "up"
                elif any(word in lower_input for word in ["set", "to"]):
                    action = "set"
                
                val_match = re.search(r'(\d+)', clean_input)
                if val_match:
                    params["value"] = int(val_match.group(1))
                    action = "set"
                params["action"] = action
                response_text = "Changing the glow of the screen, guardian."
                
            elif task == "lock_screen":
                response_text = "Hoard secured! The screen is now locked."
                
            elif task == "take_screenshot":
                response_text = "A screenshot has been captured under my wings!"
                
            elif task == "screen_record":
                action = "start"
                if any(word in lower_input for word in ["stop", "end", "finish", "halt"]):
                    action = "stop"
                params["action"] = action
                response_text = "Watching the desktop! Recording status changed, guardian."
                
            elif task == "close_window":
                response_text = "Banishment! I have closed the active window."
                
            elif task == "minimize_all":
                response_text = "Clearing the skies. All windows minimized!"
                
            elif task == "clipboard_history":
                limit = 5
                val_match = re.search(r'(\d+)', clean_input)
                if val_match:
                    limit = int(val_match.group(1))
                params["limit"] = limit
                response_text = "Peering into the scroll of memory. Here is your clipboard history."
                
            elif task == "set_reminder":
                time_match = re.search(r'(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|sec|second)s?', lower_input)
                minutes = 5.0
                if time_match:
                    amount = float(time_match.group(1))
                    unit = time_match.group(2)
                    minutes = amount
                    if "hour" in unit or "hr" in unit:
                        minutes = amount * 60
                    elif "sec" in unit:
                        minutes = amount / 60
                
                msg = "nudge"
                msg_match = re.search(r'to\s+(.+)', clean_input, re.IGNORECASE)
                if msg_match:
                    msg = clean_param(msg_match.group(1))
                else:
                    msg = clean_input
                    for word in ["remind", "me", "set", "reminder", "timer", "alarm", "nudge", "in", "for", "to"]:
                        msg = re.sub(rf'\b{word}\b', '', msg, flags=re.IGNORECASE)
                    msg = clean_param(msg)
                msg = _clean_extracted_param(msg)
                    
                params["reminder_minutes"] = minutes
                params["reminder_message"] = msg if msg else "nudge"
                response_text = "I shall remember this! I will nudge you in due time."
                
            elif task == "delete_file":
                file_q = clean_input
                for word in ["delete", "remove", "banish", "file", "scroll", "document", "get", "rid", "of"]:
                    file_q = re.sub(rf'\b{word}\b', '', file_q, flags=re.IGNORECASE)
                file_q = clean_param(file_q)
                file_q = _clean_extracted_param(file_q)
                params["file_query"] = file_q
                response_text = f"Preparing to banish the scroll {file_q}."
                
            elif task == "find_file":
                file_q = clean_input
                for word in ["find", "search", "locate", "where", "is", "for", "file", "scroll", "document", "look", "up"]:
                    file_q = re.sub(rf'\b{word}\b', '', file_q, flags=re.IGNORECASE)
                file_q = clean_param(file_q)
                file_q = _clean_extracted_param(file_q)
                params["file_query"] = file_q
                response_text = f"By the ancient winds, I shall hunt for {file_q}!"
                
            elif task == "open_app":
                app_name = clean_input
                for word in ["open", "launch", "start", "run", "summon", "app", "application", "program"]:
                    app_name = re.sub(rf'\b{word}\b', '', app_name, flags=re.IGNORECASE)
                app_name = clean_param(app_name)
                app_name = _clean_extracted_param(app_name)
                params["app_name"] = app_name
                response_text = f"By the ancient fire, I shall awaken {app_name} for you!"
                
            return {
                "task": task,
                "params": params,
                "response": response_text
            }

        return None

    def classify_offline_intent(self, user_input: str) -> tuple[str, float]:
        """
        Classifies user_input into one of the 12 offline tasks based on keyword overlap
        and Jaccard similarity. Returns (task_name, confidence).
        """
        input_tokens = _tokenize_text(user_input)
        if not input_tokens:
            return "unknown", 0.0

        scores = {}
        for task, exemplars in OFFLINE_EXEMPLARS.items():
            max_jaccard = 0.0
            for exemplar in exemplars:
                ex_tokens = _tokenize_text(exemplar)
                intersection = set(input_tokens).intersection(ex_tokens)
                union = set(input_tokens).union(ex_tokens)
                jaccard = len(intersection) / len(union) if union else 0.0
                if jaccard > max_jaccard:
                    max_jaccard = jaccard
            
            # Boost score if a high-signal keyword is present
            signal_words = HIGH_SIGNAL_KEYWORDS.get(task, set())
            has_signal = any(token in signal_words for token in input_tokens)
            
            score = max_jaccard
            if has_signal:
                score += 0.35
                
            scores[task] = score

        best_task = "unknown"
        best_score = 0.0
        for task, score in scores.items():
            if score > best_score:
                best_score = score
                best_task = task
                
        if best_score < 0.25:
            return "unknown", best_score
            
        return best_task, best_score

    def process_command(self, user_input: str) -> dict:
        """
        Processes command: prioritizes local parser for offline-compatible tasks,
        falling back to Gemini or Groq API otherwise.
        """
        # 1. Try local/offline parsing first for basic desktop commands
        local_parsed = self.parse_command_locally(user_input)
        if local_parsed:
            return local_parsed

        # 2. Ensure we have at least one working client
        if not self.gemini_client and not self.groq_client:
            return {
                "task": "unknown",
                "params": {},
                "response": "Greetings! I don't have any API keys configured. Set them up in the .env file so my magic can awaken!"
            }
            
        system_prompt = self.get_system_prompt()
        
        # 3. Try Gemini API
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_input,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                if response.text:
                    return json.loads(response.text)
            except Exception as e:
                print(f"Gemini API call failed, trying Groq fallback: {e}")
                
        # 4. Try Groq API
        if self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                content = chat_completion.choices[0].message.content
                if content:
                    return json.loads(content)
            except Exception as e:
                print(f"Groq API call failed: {e}")
                
        # Fallback response in case both models fail or JSON is corrupted
        return {
            "task": "unknown",
            "params": {},
            "response": "Whoops! The magic is fading slightly (API error). Let's try again in a moment!"
        }

    def generate_direct_response(self, prompt: str, context: str) -> str:
        """
        Helper method to generate natural text responses from Aether
        using a text prompt and supporting context (e.g. for summarizing text or web search).
        """
        system_prompt = (
            "You are Aether, a small ancient dragon desktop companion. Write a short, "
            "helpful, and wise response in Aether's dragon persona answering the user's prompt based on the provided context. "
            "Keep it under 3-4 sentences. Keep it mystical, motivating, and warm!"
        )
        
        # 1. Try Gemini
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Context:\n{context}\n\nUser Request:\n{prompt}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7
                    )
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"Gemini text generation failed: {e}")
                
        # 2. Try Groq
        if self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context:\n{context}\n\nUser Request:\n{prompt}"}
                    ],
                    temperature=0.7
                )
                content = chat_completion.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                print(f"Groq text generation failed: {e}")
                
        return "Sorry, my dragon magic couldn't summarize this scroll. My head hurts from reading all this text!"
