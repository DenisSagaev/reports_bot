from environs import Env

env = Env()
env.read_env(r"C:\my_projects\reports_bot\.env")

tg_bot_token = env('BOT_TOKEN')  # Токен для доступа к телеграм-боту
