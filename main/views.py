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

    # Teacher.objects.all().delete()
    # Student.objects.all().delete()
    # GameProfile.objects.all().delete()
    # Game.objects.all().delete()

    # print(User.objects.filter(is_superuser = False, teacher__isnull = True))
    # non_superusers = User.objects.filter(is_superuser = False)
    # non_superusers.delete()

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