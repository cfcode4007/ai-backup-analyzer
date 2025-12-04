import os
import logging
from datetime import datetime
from collections import deque

import requests
from ailib import Payload
from Preferences import Preferences

# GPT Home Assistant wrapper over Payload, ChatHistoryManager, Config, ModelConnection, PromptBuilder 
class AIBackupAnalyzer:

    version = "0.0.3"
    # Version 0.0.3:
    # - Simplified output to a more notification-friendly form, and it will now be sent as one if the backup log yields unexpected results
    # Version 0.0.2:
    # - Modified the user input debug message to keep most recent logs and split into multiple lines for readability

    log_file = ""

    def __init__(self, preferences_file: str):
        # Instantiate Settings/Prefs
        self.preferences = Preferences(preferences_file)

        # Load up settings/preferences and then instantiate Payload with preferred config
        prompts_file = self.preferences.get_setting_val("Prompts File")
        chat_hist_file = self.preferences.get_setting_val("Chat History File")
        self.log_file = self.preferences.get_setting_val("Log File")
        log_mode = self.preferences.get_setting_val("Log Mode")

        # Setup Log file and current mode (Debug or Info)
        self._configure_logging(log_mode)

        # Load Open AI Key from environment variable, or settings/prefs for backward compatability
        api_key = self._load_openai_key()
        if api_key == "":
            api_key = self.preferences.get_setting_val("OpenAI Key")                

        # Instantiate Payload with settings values retrieved
        self.payload = Payload(prompts_file, chat_hist_file, api_key)

    def _load_openai_key(self):
        # Get key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")

        if api_key is None:
            logging.error("OPENAI_API_KEY not found in environment variables")
            return ""

        else:
            return api_key
        
    def _load_ha_token(self):
        # Get token from environment variables
        ha_token = os.getenv("HA_TOKEN")

        if ha_token is None:
            logging.error("HA_TOKEN not found in environment variables")
            return ""

        else:
            return ha_token

    def _configure_logging(self, log_mode: str):
        """Debug for DEBUG mode, Anything else for INFO"""
        # Default logging level set to Info but override to DEBUG with parameter
        log_level = logging.INFO

        if log_mode.lower() == "debug":
            log_level = logging.DEBUG

        logging.basicConfig(
            filename=self.log_file,
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        ) 

    def _send_notification(self, notification_type: str):
        # Load Home Assistant Token from environment variable
        ha_token = self._load_ha_token()

        url = "http://192.168.123.199:8123/api/services/notify/mobile_app_sm_g975w"
        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json"
        }
        data = {
            "message": f"The Server02 ZFS backup did not complete successfully ({notification_type})."
        }
        response = requests.post(url, headers=headers, json=data)
        logging.info(f'HTTP Response: POST {url} "{response.status_code} {response.text}"')        

    def get_backup_data(self, input_file):
        """Retrieve backup data from the Server."""
        # Resolve file path relative to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, input_file)

        try:
            # Keep the most recent 20 non-empty lines (preserve order)
            last_lines = deque(maxlen=20)
            with open(input_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        last_lines.append(line)

            backup_data = list(last_lines)

        except FileNotFoundError:
            raise FileNotFoundError(f"Backup log file not found: {input_path}")
        return backup_data
    
    def determine_log_status(self, ai_reply: str):
        """Determine based on analysis of a log if it failed or encountered an abnormality at all, in which case send a notification."""
        keyword_failed = "Failed"
        keyword_abnormality = "Abnormality"

        if keyword_failed in ai_reply:
            logging.info(f"Sending notification for incomplete backup ({keyword_failed})")
            self._send_notification(keyword_failed)
        else:
            # Count any abnormality as not necessarily a failure but something that will appear in a notification
            if keyword_abnormality in ai_reply:
                logging.info(f"Sending notification for incomplete backup ({keyword_abnormality})")
                self._send_notification(keyword_abnormality)   
        

# ============================================================= M A I N ==================================================

    def main(self):
        input_file = 'sample_backup_data.log'

        # Indicate start of the log for this run of the program
        logging.info("\n💡")
        logging.info(f"AI Backup Analyzer v{self.version} class currently using ModelConnection v{self.payload.connection.version}, PromptBuilder v{self.payload.prompts.version}, ChatHistoryManager v{self.payload.history.version}, Preferences v{self.preferences.version}, Payload v{self.payload.version}")      

        # Initialize AI analyzer
        prompt = "backupshort"
        self.payload.prompts.load_prompt(prompt)        
        self.payload.connection.set_maximum_tokens(500)
        
        # GPT 5 mini
        self.payload.connection.set_model("gpt-5-mini")        
        self.payload.connection.set_verbosity("low")
        self.payload.connection.set_reasoning_effort("minimal")

        # GPT 4o mini
        # self.payload.connection.set_model("gpt-4o-mini")        

        # GPT 5 nano
        # self.payload.connection.set_model("gpt-5-nano")        
        # self.payload.connection.set_verbosity("low")
        # self.payload.connection.set_reasoning_effort("minimal")

        # Get the current date in a format that matches the incoming log lines for AI context        
        # current_date = datetime.now().strftime('%Y-%m-%d')
        current_date = '2025-11-28'
        # Add dynamic information to the prompt below system instructions        
        prompt_addendum = f"The Current Date is [{current_date}]\n"        
        backup_to_analyze = self.get_backup_data(input_file)
        
        user_message = "Analyze the preceding backup log."

        # Prepare and send message to AI
        logging.info(f"Model: {self.payload.connection.model}, Verbosity: {self.payload.connection.verbosity}, Reasoning: {self.payload.connection.reasoning_effort}, Max Tokens: {self.payload.connection.maximum_tokens}")
        # Format backup lines as a multiline string for easier debugging (one line per entry, indented)
        if isinstance(backup_to_analyze, list):
            backup_text = "\n".join(f"  {line}" for line in backup_to_analyze)
        else:
            backup_text = str(backup_to_analyze)

        logging.debug(f"Payload \n\nSystem Prompt: {self.payload.prompts.get_prompt()} \n\nSpecial/Dynamic Content: {prompt_addendum} \n{backup_text} \n\nUser Message: {user_message}")
        # We don't want to automatically add the AI response to chat history since it will be full of json
        # for the entities, devices, data, variables etc.  The important thing is to keep chat context
        # Therefore, we turn off auto, clean up response before logging both user/assistant messages to keep sync
        self.payload.Auto_Add_AI_Response_To_History = False

        prompt_addendum += f"Backup Log to Analyze: {backup_text}"

        # Send the user mesage to AI and receive the response
        reply = self.payload.send_message(user_message, prompt, prompt_addendum)
        # reply = "Abnormality found in incremental backup for s2Pool/Incus/containers at 2025-11-28 16:05:35: No confirmation of completion found. Successfully completed incremental backup for s2Pool/ROOT/rPool at 2025-11-28 16:01:12. Successfully completed incremental backup for s2Pool/VMz at 2025-11-28 16:01:36."
        logging.info(f"Assistant Raw Reply: {reply}")

        # Take the AI reply and programmatically determine if the overall transaction failed or encountered an abnormality
        self.determine_log_status(reply)

        return f"Program ran successfully at {str(datetime.now())}"

if __name__ == "__main__":
    # Change the current working directory to this script for imports and relative pathing
    program_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(program_path)

    wrapper = AIBackupAnalyzer("ai_backup_analyzer.json")

    response_output = wrapper.main()
  
    print(f"{response_output}")
    
    
