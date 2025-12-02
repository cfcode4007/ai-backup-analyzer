from ailib import Payload
from Preferences import Preferences
import os
import logging
from datetime import datetime

# GPT Home Assistant wrapper over Payload, ChatHistoryManager, Config, ModelConnection, PromptBuilder 
class AIBackupAnalyzer:

    version = "0.0.1"

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
            api_key = self.config.get_setting_val("OpenAI Key")

        # Instantiate Payload with settings values retrieved
        self.payload = Payload(prompts_file, chat_hist_file, api_key)

    def _load_openai_key(self):
        # Get key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")

        if api_key is None:
            logging.info("OPENAI_API_KEY not found in environment variables")
            return ""

        else:
            return api_key

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

    def get_backup_data(self, input_file):
        """Retrieve backup data from the Server."""
        # if not input_file:
        #     raise ValueError("Usage: get_ha_entity_info(<entity_list_file>)")

        # Resolve file path relative to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, input_file)

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                backup_data = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Entity list file not found: {input_path}")
        
        # Previous backup data for testing
        # backup_data = "[2025-11-30 16:07:01] ⚙ Processing Dataset (s2Pool/ROOT/rPool → server01/backup/server02/rPool)"
        # backup_data += "\n[2025-11-30 16:07:15] ✅ Incremental Backup Completed (s2Pool/ROOT/rPool → server01/backup/server02/rPool)"
        # backup_data += "\n[2025-11-30 16:07:15] ⚙ Processing Dataset (s2Pool/VMz → server01/backup/server02/VMz)"
        # backup_data += "\n[2025-11-30 16:07:44] ✅ Incremental Backup Completed (s2Pool/VMz → server01/backup/server02/VMz)"
        # backup_data += "\n[2025-11-30 16:07:44] ⚙ Processing Dataset (s2Pool/Incus/containers → server01/backup/server02/Incus/containers)"
        # backup_data += "\n[2025-11-30 16:11:40] ✅ Incremental Backup Completed (s2Pool/Incus/containers → server01/backup/server02/Incus/containers)"
        # backup_data += "\n[2025-11-30 16:11:40] Script /usr/local/bin/zfs-backup.sh completed."
        # backup_data += "\n[2025-11-30 16:11:40] *****************************************************************************************"
        # backup_data += "\n[2025-12-01 16:00:59] *****************************************************************************************"
        # backup_data += "\n[2025-12-01 16:00:59] Script /usr/local/bin/zfs-backup.sh starting at 2025-12-01 16:00:59"
        # backup_data += "\n[2025-12-01 16:00:59] Using config file: /usr/local/etc/zfs-backup.conf"
        # backup_data += "\n[2025-12-01 16:00:59] Using log file: /var/log/zfs-backup.log"
        # backup_data += "\n[2025-12-01 16:00:59] ⚙ Processing Dataset (s2Pool/ROOT/rPool → server01/backup/server02/rPool)"
        # backup_data += "\n[2025-12-01 16:01:16] ✅ Incremental Backup Completed (s2Pool/ROOT/rPool → server01/backup/server02/rPool)"
        # backup_data += "\n[2025-12-01 16:01:16] ⚙ Processing Dataset (s2Pool/VMz → server01/backup/server02/VMz)"
        # backup_data += "\n[2025-12-01 16:01:49] ✅ Incremental Backup Completed (s2Pool/VMz → server01/backup/server02/VMz)"
        # backup_data += "\n[2025-12-01 16:01:49] ⚙ Processing Dataset (s2Pool/Incus/containers → server01/backup/server02/Incus/containers)"
        # backup_data += "\n[2025-12-01 16:05:51] ✅ Incremental Backup Completed (s2Pool/Incus/containers → server01/backup/server02/Incus/containers)"
        # backup_data += "\n[2025-12-01 16:05:51] Script /usr/local/bin/zfs-backup.sh completed."
        # backup_data += "\n[2025-12-01 16:05:51] *****************************************************************************************"

        return backup_data

# ============================================================= M A I N ==================================================

    def main(self):
        # Indicate start of the log for this run of the program
        logging.info("\n💡")
        logging.info(f"AI Backup Analyzer v{self.version} class currently using ModelConnection v{self.payload.connection.version}, PromptBuilder v{self.payload.prompts.version}, ChatHistoryManager v{self.payload.history.version}, Preferences v{self.preferences.version}, Payload v{self.payload.version}")      

        # Initialize AI analyzer
        self.payload.connection.set_model("gpt-5-mini")        
        self.payload.connection.set_maximum_tokens(500)
        self.payload.connection.set_verbosity("low")
        self.payload.connection.set_reasoning_effort("minimal")
        self.payload.prompts.load_prompt("backup")
        self.payload.history.load_history("default")
        logging.info("!!!! History is currently being Reset for each interaction !!!!")
        self.payload.history.reset_history()

        # Get the current date in a format that matches the incoming log lines for AI context        
        # current_date = datetime.now().strftime('%Y-%m-%d')
        current_date = '2025-12-01'
        # Add dynamic information to the prompt below system instructions        
        prompt_addendum = f"\n\nUSER INPUT\nCurrent Date: [{current_date}]\nRaw Backup Log Lines:"
        backup_to_analyze = self.get_backup_data('sample_backup_data.log')
        
        # Prepare and send message to AI
        logging.info(f"Model: {self.payload.connection.model}, Verbosity: {self.payload.connection.verbosity}, Reasoning: {self.payload.connection.reasoning_effort}, Max Tokens: {self.payload.connection.maximum_tokens}")
        logging.info(f"User Message: \n{self.payload.prompts.get_prompt()} \n{prompt_addendum} \n{backup_to_analyze}")
        # We don't want to automatically add the AI response to chat history since it will be full of json
        # for the entities, devices, data, variables etc.  The important thing is to keep chat context
        # Therefore, we turn off auto, clean up response before logging both user/assistant messages to keep sync
        self.payload.Auto_Add_AI_Response_To_History = False
        # Send the user mesage to AI and receive the response
        reply = self.payload.send_message(backup_to_analyze, 'backup', prompt_addendum)
        logging.info(f"Assistant Raw Reply: {reply}")        
        return reply


if __name__ == "__main__":
    # Change the current working directory to this script for imports and relative pathing
    program_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(program_path)

    wrapper = AIBackupAnalyzer("ai_backup_analyzer.json")

    ai_response = wrapper.main()
  
    print(f"AI Response: {ai_response}")
    
    
