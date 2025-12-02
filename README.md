## AI Backup Analyzer

A personal-use program that:
- Reads contents of a specified backup log file
- Prompts an AI such that it will analyze the contents and respond with status lines for all major backups or attempts
- Sends returned lines as notifications for HA system.

It will run once daily to save human time opening and scanning through it.
Different from other programs of mine is, mainly, its usage of classes as packages in Python and HA operations being on the front-end.