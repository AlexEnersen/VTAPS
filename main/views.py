from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from main.models import User
from teacher.models import Teacher, Game
from student.models import Student
from game.models import GameProfile
import boto3
import os
import environ
import watchtower, logging
import pandas as pd
from io import StringIO

from django.contrib.auth import logout


environment = os.environ['ENV']

secret_name = "S3_Keys"
region_name = "us-east-1"

if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

try:
    if environment == 'prod':
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        SECRET_KEY = eval(get_secret_value_response['SecretString'])
        s3_access_key = SECRET_KEY['S3_ACCESS_KEY_ID']
        s3_secret_key = SECRET_KEY['S3_SECRET_ACCESS_KEY']
        
    else:
        env = environ.Env()
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
        s3_access_key = env('S3_ACCESS_KEY_ID')
        s3_secret_key = env('S3_SECRET_ACCESS_KEY')

    s3 = boto3.client("s3", aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)

except Exception as error:
    if environment == 'prod':
        logger.info('error:', error)
    else:
        print('Error:', error)

def home(response):    
    game_id = response.session.get("game_id", None)
    if hasattr(response.user, "student"):
        return redirect('/student')
    elif hasattr(response.user, "teacher"):
        return redirect("/teacher")
    else:
        return render(response, 'main/home.html', {"game_id": game_id})

def reset(response):
    
    game_id = response.session.get("game_id", None)
    currentGames = GameProfile.objects.filter(id = game_id)
    currentGames.delete()
    if game_id:
        del response.session['game_id']
    
    logout(response)
    # Teacher.objects.all().delete()
    # Student.objects.all().delete()
    # GameProfile.objects.all().delete()
    # Game.objects.all().delete()
    # superusers = User.objects.filter(is_superuser = True)
    # non_superusers.delete()
    
    # print(User.objects.filter(is_superuser = False, teacher__isnull = True))

    # import io
    # import os
    # import sys
    # import zipfile

    # # ----------------------------- EDIT THESE ---------------------------------
    # GAME_IDS = [2156, 2083, 2031, 2216, 2539, 4643, 4646, 4698]                 # <-- Game ids (teacher.models.Game.id)
    # OUTPUT_DIR = "weather_downloads"     # created if missing
    # DJANGO_SETTINGS_MODULE = "vtaps.settings"   # <-- change to your project's settings module
    # SAVE_RAW_ZIP = True                  # also keep the original zip from S3
    # # --------------------------------------------------------------------------

    # os.environ.setdefault("ENV", "dev")
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    # sys.path.insert(0, os.getcwd())

    # import django  # noqa: E402
    # django.setup()

    # from teacher.models import Game      # noqa: E402
    # from game.views import s3            # noqa: E402  (reuses the configured boto3 client)

    # WEATHER_BUCKET = "vtapsweatherbucket"

    # print("Hello")

    # def download_for_game(game_id):
    #     try:
    #         game = Game.objects.get(id=game_id)
    #     except Game.DoesNotExist:
    #         print(f"[game {game_id}] not found in database, skipping")
    #         return False

    #     weather_file = game.weatherFile
    #     if not weather_file:
    #         print(f"[game {game_id}] has no weatherFile set, skipping")
    #         return False

    #     out_dir = os.path.join(OUTPUT_DIR, f"game_{game_id}")
    #     os.makedirs(out_dir, exist_ok=True)

    #     try:
    #         buffer = io.BytesIO()
    #         s3.download_fileobj(WEATHER_BUCKET, weather_file, buffer)
    #         buffer.seek(0)

    #         if SAVE_RAW_ZIP:
    #             with open(os.path.join(out_dir, os.path.basename(weather_file)), "wb") as f:
    #                 f.write(buffer.getvalue())

    #         found = []
    #         with zipfile.ZipFile(buffer) as z:
    #             for name in z.namelist():
    #                 if name in ("weather.txt", "forecast.txt"):
    #                     with open(os.path.join(out_dir, name), "wb") as f:
    #                         f.write(z.read(name))
    #                     found.append(name)

    #         if not found:
    #             print(f"[game {game_id}] zip {weather_file} had no weather.txt/forecast.txt")
    #             return False

    #         print(f"[game {game_id}] saved {', '.join(found)} ({weather_file}) -> {out_dir}")
    #         return True

    #     except Exception as error:
    #         # views.py falls back to a local copy in weather_files/, so do the same
    #         local = os.path.join("weather_files", weather_file)
    #         if os.path.exists(local):
    #             with open(local, "r") as src, open(os.path.join(out_dir, os.path.basename(weather_file)), "w") as dst:
    #                 dst.write(src.read())
    #             print(f"[game {game_id}] S3 failed ({error}); copied local fallback {local}")
    #             return True
    #         print(f"[game {game_id}] FAILED: {error}")
    #         return False



    # ok = sum(download_for_game(gid) for gid in GAME_IDS)
    # print(f"\nDone: {ok}/{len(GAME_IDS)} games downloaded to ./{OUTPUT_DIR}")




    return redirect("/")

def downloadResults(response):
    dataFrames = []

    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket='finalresultsbucket'):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            keys.append(key)

    for key in keys:
        obj = s3.get_object(Bucket='finalresultsbucket', Key=key)
        csv_str = obj["Body"].read().decode("utf-8")
        df = pd.read_csv(StringIO(csv_str))
        print("DF:", df)
        dataFrames.append(df)

    outputDir = f'../finalResults'    

    os.makedirs(outputDir, exist_ok=True)
    singleCSV = pd.concat(dataFrames, ignore_index=True).sort_values(by="Team ID")
    singleCSV.to_csv(f"{outputDir}/Day 2 Raw Results.csv", index=False)
    
    return redirect("/")