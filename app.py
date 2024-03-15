import io
import json
import os
import shutil
import uuid
from flask import Flask, jsonify, render_template, Response, request, redirect, url_for, session, send_from_directory, abort, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
from flask_bcrypt import Bcrypt
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from google.cloud import translate_v2
from werkzeug.utils import secure_filename
from io import BytesIO
import threading
import time
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import wave
import librosa
from pydub import AudioSegment
import numpy as np
  
app = Flask(__name__)
  
app.secret_key = 'xyzsdfg'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'octavewebapp'
  
mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Load model
# model1 = MusicGen.get_pretrained('facebook/musicgen-melody')
# model2 = MusicGen.get_pretrained('facebook/musicgen-small')
# model1.set_generation_params(duration=8)
# model2.set_generation_params(duration=8)


def delete_file_later(file_path, delay):
    print("in delete_file_later method")
    time.sleep(delay)  # รอเวลาที่กำหนด
    print(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
        print("already removed")

def translate_THToENG(descriptions) :
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"
    translate_client = translate_v2.Client()
    text = descriptions
    target = "en"
    output = translate_client.translate(text,target_language=target)
    return output

def list_to_str(list):
    str = ''
    for text in list:
        str+= " " + text
    str = str[1:]
    print("str: " + str)    
    return str

def emotion_translate(emotion):
    emotion_TH = ""
    emotion_translation = {
                "happy": "ดีใจ",
                "fun": "สนุกสนาน",
                "cheerful": "ร่าเริง",
                "sweet": "หวาน",
                "love": "รัก",
                "encouragement": "มีกำลังใจ",
                "sad": "เศร้า",
                "angry": "โกรธ",
                "stressful": "เครียด",
                "discouragement": "ท้อถอย"
    }
    for e in emotion:
        emotion_TH += " #" +emotion_translation[e]
    return  emotion_TH
def musinIns_translate(music_instruments):
    musinIns_TH = ""
    instrument_translation = {
        "Guitar": "กีตาร์",
        "Bass": "เบส",
        "Violin": "ไวโอลิน",
        "Viola": "วิโอลา",
        "Cello": "เชลโล",
        "DoubleBass": "ดับเบิลเบส",
        "Harp": "ฮาร์ป",
        "Banjo": "แบนโจ",
        "Mandolin": "แมนโดลิน",
        "Lute": "ลูท",
        "Lyre": "ไลร์",
        "DrumSet": "กลองชุด",
        "Timpani": "กลองทิมปานี",
        "BigDrum": "กลองใหญ่",
        "SmallDrum": "กลองเล็ก",
        "BongoDrum": "กลองบองโก",
        "CongaDrum": "กลองคองกา",
        "Tambourine": "แทมบูรีน",
        "Cymbal": "ฉาบ",
        "Bellaila": "เบลไลลา",
        "Xylophone": "ไซโลโฟน",
        "Vibraphone": "ไวบราโฟน",
        "LineBell": "ไลน์เบล",
        "Triangle": "ไทรแองเกิล",
        "Castanet": "คาสทาเนท",
        "Maracas": "มาราคัส",
        "Cabaza": "คาบาซา",
        "Marimba": "มาริมบา",
        "Cowbell": "คาวเบล",
        "TubularBells": "ระฆังราว",
        "Organ": "ออร์แกน",
        "Melodian": "เมโลเดียน",
        "Piano": "เปียโน",
        "Accordion": "แอคคอร์เดียน",
        "Harpsichord": "ฮาร์ปซิคอร์ด",
        "Electone": "อิเล็กโทน",
        "Clavichord": "แคลฟวิคอร์ด",
        "OrganMount": "เมาท์ออแกน",
        "Flute": "ฟลูต",
        "Saxophone": "แซกโซโฟน",
        "Oboe": "โอโบ",
        "Clarinet": "คลาริเน็ต",
        "Bassoon": "บาสซูน",
        "Recorder": "รีคอร์เดอร์",
        "Piccolo": "ปิคโคโล",
        "CorAnglais": "คอร์ แองเกลส์",
        "Trombone": "ทรอมโบน",
        "Trumpet": "ทรัมเป็ต",
        "Tuba": "ทูบา",
        "Flugelhorn": "ฟลูเกลฮอร์น",
        "FrenchHorn": "เฟรนช์ฮอร์น",
        "Cornet": "คอร์เน็ท",
        "Sousaphone": "ซูซาโฟน",
        "Euphonium": "ยูโฟเนียม"
    }
    for m in music_instruments:
        musinIns_TH += " #" +instrument_translation[m]
    return musinIns_TH    

def songtype_translate(song_type):
    song_type_translation = {
                            "Instrumental": "เพลงบรรเลง",
                            "Classic": "คลาสสิก",
                            "POP": "ป๊อป",
                            "Jazz": "แจ๊ส",
                            "R&B": "ริทึมแอนด์บลูส์",
                            "Hiphop": "ฮิปฮอป",
                            "Rock": "ร็อก",
                            "Electronic": "อิเล็กทรอนิกส์"
                        }
    
    song_type_TH = " #" + song_type_translation[song_type] 
    
    return song_type_TH  
    
def list_to_str_withAnd(list):
    str = ''
    for text in list:
        str+= " " + text + " and"
    str = str[1:-4]
    print("str: " + str)    
    return str

def generateSong(full_description):

    if 'guiding_audio_file' in request.files and request.files['guiding_audio_file'].filename != '':
        
        model1 = MusicGen.get_pretrained('facebook/musicgen-melody')
        model1.set_generation_params(duration=10)

        content_length = request.content_length
        if content_length and content_length > 10 * 1024 * 1024:  # 10 MB
            message = "ขนาดไฟล์ใหญ่เกินไป กรุณาอัปโหลดไฟล์ที่มีขนาดไม่เกิน 10 MB"
            return render_template('genSong.html', audio_generated=False, message=message)
        
        guiding_audio_file = request.files['guiding_audio_file']
        print("guiding_audio_file",guiding_audio_file)
        # Generate a unique filename 
        unique_filename = str(uuid.uuid4())

        original_filename = guiding_audio_file.filename
        file_basename, file_extension = os.path.splitext(original_filename)
        file_extension = file_extension.lower()

        # original_filename = secure_filename(guiding_audio_file.filename)
        # file_extension = original_filename.rsplit('.', 1)[1].lower()  
        
        uploaded_file_path = os.path.join('song_files/guideSong_files', f"{unique_filename}.{file_extension}")
        guiding_audio_file.save(uploaded_file_path)
        
        if file_extension in ['mp3', 'm4a']:
            # Convert to WAV using pydub
            audio = AudioSegment.from_file(uploaded_file_path)
            guide_file_path = os.path.join('song_files/guideSong_files', f"{unique_filename}.wav")
            audio.export(guide_file_path, format="wav")
        else:
            guide_file_path = uploaded_file_path

        print("guiding_audio_file exists")
        
        melody, sr = torchaudio.load(guide_file_path, format="wav")
        
        wav = model1.generate_with_chroma(full_description, melody, sr)
        print("Guiding audio file is used for generating music.")

        threading.Thread(target=delete_file_later, args=(guide_file_path, 600)).start()  

        # Generate a unique filename 
        filename = secure_filename(f"{uuid.uuid4()}.wav")
        file_path = os.path.join('song_files/genSong_files', filename)
        session['file_path'] = file_path
        torchaudio.save(file_path, format="wav", src=wav[0], sample_rate=model1.sample_rate)

        # สร้างและเริ่ม thread ที่จะลบไฟล์หลังจาก 20 นาที
        threading.Thread(target=delete_file_later, args=(file_path, 1200)).start()    
    else:
        model2 = MusicGen.get_pretrained('facebook/musicgen-small')
        model2.set_generation_params(duration=10)

        print("guiding_audio_file not exists")
        wav = model2.generate(full_description)

        # Generate a unique filename 
        filename = secure_filename(f"{uuid.uuid4()}.wav")
        file_path = os.path.join('song_files/genSong_files', filename)
        # session['file_path'] = file_path
        torchaudio.save(file_path, format="wav", src=wav[0], sample_rate=model2.sample_rate)

        # สร้างและเริ่ม thread ที่จะลบไฟล์หลังจาก 10 นาที
        threading.Thread(target=delete_file_later, args=(file_path, 600)).start()
    
    return filename

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':   

        descriptionTH = request.form['descriptions']
        print("descriptionTH: "+ descriptionTH)

        descriptionENG = translate_THToENG(descriptionTH)
        print(descriptionENG)

        descriptions = [descriptionENG['translatedText']]
        print("descriptions: " + str(descriptions))

        full_description = ""
        emotion_descriptionTH = ""
        song_type_descriptionTH = ""
        musinIns_descriptionTH = ""

        if 'emotion' in request.form :          
            emotion = request.form.getlist('emotion')
            print("emotion: ")
            emotion_str = list_to_str(emotion)
            full_description += emotion_str

            emotion_descriptionTH = emotion_translate(emotion)

        if 'song-type' in request.form :    
            song_type = request.form['song-type']
            # print("song-type: "+ song_type)
            full_description += " " + song_type + " song"

            song_type_descriptionTH = songtype_translate(song_type)

        if 'music-instrument' in request.form :   
            music_instruments = request.form.getlist('music-instrument')
            print("music_instruments: ")
            instruments_str = list_to_str_withAnd(music_instruments)
            full_description += " with " + instruments_str

            musinIns_descriptionTH = musinIns_translate(music_instruments)

        full_description += " " + descriptions[0]
        full_descriptionTH = descriptionTH + musinIns_descriptionTH + emotion_descriptionTH + song_type_descriptionTH

        print("full_description: "+ full_description)
        print("full_descriptionTH: "+ full_descriptionTH)

        full_description_list = []
        full_description_list.append(full_description)

        if full_description.strip() != "":
            filename = generateSong(full_description_list)

            return render_template('genSong.html', audio_generated=True , filename=filename, full_descriptionTH=full_descriptionTH)       
        else:
            return render_template('genSong.html', audio_generated=False)
    else:
            return render_template('genSong.html', audio_generated=False)
    
@app.route('/homeGenEng', methods=['GET', 'POST'])
def homeGenEng():
    if request.method == 'POST':   

        descriptions = request.form['descriptions']
        print("description: "+ descriptions)

        full_description = ""
        emotion_descriptionTH = ""
        song_type_descriptionTH = ""
        musinIns_descriptionTH = ""

        if 'emotion' in request.form :          
            emotion = request.form.getlist('emotion')
            print("emotion: ")
            emotion_str = list_to_str(emotion)
            full_description += emotion_str

            emotion_descriptionTH = emotion_translate(emotion)

        if 'song-type' in request.form :    
            song_type = request.form['song-type']
            # print("song-type: "+ song_type)
            full_description += " " + song_type + " song"

            song_type_descriptionTH = songtype_translate(song_type)

        if 'music-instrument' in request.form :   
            music_instruments = request.form.getlist('music-instrument')
            print("music_instruments: ")
            instruments_str = list_to_str_withAnd(music_instruments)
            full_description += " with " + instruments_str

            musinIns_descriptionTH = musinIns_translate(music_instruments)

        full_description += " " + descriptions
        full_descriptionENG = descriptions + musinIns_descriptionTH + emotion_descriptionTH + song_type_descriptionTH

        print("full_description: "+ full_description)
        print("full_descriptionENG: "+ full_descriptionENG)


        full_description_list = []
        full_description_list.append(full_description)

        if full_description.strip() != "":
            filename = generateSong(full_description_list)

            return render_template('genSongEng.html', audio_generated=True , filename=filename, full_description=full_descriptionENG)       
        else:
            return render_template('genSongEng.html', audio_generated=False)
    else:
            return render_template('genSongEng.html', audio_generated=False)

@app.route('/stream/<filename>')
def stream(filename):
    music_directory = os.path.join(app.root_path, 'song_files', 'genSong_files')
    if not os.path.exists(os.path.join(music_directory, filename)):
        abort(404)
    return send_from_directory(music_directory, filename, as_attachment=True)

@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            session['dateOfBirth'] = user['dateOfBirth'].strftime('%Y-%m-%d')
            session['gender'] = user['gender']
            mesage = 'Logged in successfully !'
            return redirect(url_for('genSong'))
            
            # return render_template('genSong_login.html', mesage = mesage)
        else:
            mesage = '**กรุณาใส่อีเมลและรหัสผ่านให้ถูกต้อง'
    return render_template('login.html', mesage = mesage)
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    session.pop('dateOfBirth', None)
    session.pop('gender', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods =['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'dateOfBirth' in request.form and 'gender' in request.form and 'password' in request.form and 'confirmPassword' in request.form:
        userName = request.form['name']
        email = request.form['email']

        dateOfBirth_str = request.form['dateOfBirth']
        def validate_date_format(date_str):
            try:
                # พยายามแปลงเป็น datetime
                datetime.strptime(date_str, '%Y-%m-%d')
                return True
            except ValueError:
                # กรณีที่ไม่สามารถแปลงได้
                return False
                
        if validate_date_format(dateOfBirth_str) :
            dateOfBirth = datetime.strptime(dateOfBirth_str, '%Y-%m-%d').date()
            checkDate = True
        else:
            checkDate = False

        gender = request.form['gender']

        password1 = request.form['password']
        password2 = request.form['confirmPassword']
       
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()

        if account:
            # Account already exists !
            mesage = 'คุณมีบัญชีผู้ใช้อยู่แล้ว'
        elif not userName or not email or not dateOfBirth_str or not gender or not password1 or not password2:
            # Please fill out the form !
            mesage = 'กรุณากรอกข้อมูลให้ครบถ้วน'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            # Invalid email address !
            mesage = 'กรุณากรอกข้อมูลให้ถูกต้อง'
        elif checkDate == False:
            mesage = 'กรุณากรอกวันที่ให้ถูกต้อง ตัวอย่างเช่น 31/01/2001'
        elif password1 != password2:
            mesage = 'รหัสผ่านไม่ตรงกัน กรุณากรอกข้อมูลอีกครั้ง'
        elif len(password1) < 6:
            mesage = 'รหัสผ่านต้องมีมากกว่าหรือเท่ากับ 6 อักขระ กรุณากรอกข้อมูลอีกครั้ง'
        else:
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s, % s, % s)', (userName, email, dateOfBirth, gender, hashed_password, ))
            mysql.connection.commit()
            # You have successfully registered !
            message = 'สร้างบัญชีผู้ใช้สำเร็จแล้ว'
            return render_template('regisSuccess.html', message = message)
    elif request.method == 'POST':
        # Please fill out the form !
        mesage = 'กรุณากรอกข้อมูลให้ครบถ้วน'
    return render_template('register.html', mesage = mesage)
    
@app.route('/profile')
def profile():
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    return  render_template('profile_login.html')

@app.route('/changePassword', methods=['GET', 'POST'])
def changePassword():
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    message = ''
    if request.method == 'POST' and 'password' in request.form and 'confirmPassword' in request.form:
        user_id = session.get('userid')
        
        new_password = request.form['password']
        confirm_password = request.form['confirmPassword']
        
        if new_password != confirm_password:
            message = 'รหัสผ่านไม่ตรงกัน กรุณากรอกข้อมูลอีกครั้ง'
        elif len(new_password) < 6:
            message = 'รหัสผ่านต้องมีมากกว่าหรือเท่ากับ 6 อักขระ กรุณากรอกข้อมูลอีกครั้ง'
        else:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE user SET password = %s WHERE userid = %s', (hashed_password, user_id))
            mysql.connection.commit()
            message = 'เปลี่ยนรหัสผ่านเรียบร้อยแล้ว'
            return render_template('changePwSuccess.html')
            # return redirect(url_for('profile'))
        
    return render_template('changePassword.html', message=message)

@app.route('/genSong', methods=['GET', 'POST'])
def genSong():
    if not session.get('userid'):
        return redirect(url_for('login'))

  
    if request.method == 'POST':   

        user_id = session.get('userid')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT COUNT(*) AS song_count FROM gensong_user WHERE userid = %s', (user_id,))
        song_count_result = cursor.fetchone()
        mysql.connection.commit()
        cursor.close()

        song_count = 0

        if song_count_result:
            song_count = song_count_result['song_count'] +1
            print(f'จำนวนเพลงสำหรับผู้ใช้ {user_id} คือ {song_count}')
        

        descriptionTH = request.form['descriptions']
        print("descriptionTH: "+ descriptionTH)

        descriptionENG = translate_THToENG(descriptionTH)
        print(descriptionENG)

        descriptions = [descriptionENG['translatedText']]
        print("descriptions: " + str(descriptions))

        full_description = ""
        emotion_descriptionTH = ""
        song_type_descriptionTH = ""
        musinIns_descriptionTH = ""

        if 'emotion' in request.form :          
            emotion = request.form.getlist('emotion')
            print("emotion: ")
            emotion_str = list_to_str(emotion)
            full_description += emotion_str

            emotion_descriptionTH = emotion_translate(emotion)

        if 'song-type' in request.form :    
            song_type = request.form['song-type']
            # print("song-type: "+ song_type)
            full_description += " " + song_type + " song"

            song_type_descriptionTH = songtype_translate(song_type)


        if 'music-instrument' in request.form :   
            music_instruments = request.form.getlist('music-instrument')
            print("music_instruments: ")
            instruments_str = list_to_str_withAnd(music_instruments)
            full_description += " with " + instruments_str

            musinIns_descriptionTH = musinIns_translate(music_instruments)
            

        full_description += " " + descriptions[0]
        full_descriptionTH = descriptionTH + musinIns_descriptionTH + emotion_descriptionTH + song_type_descriptionTH


        print("full_description: "+ full_description)
        print("full_descriptionTH: "+ full_descriptionTH)

        full_description_list = []
        full_description_list.append(full_description)

        if full_description.strip() != "":
            filename = generateSong(full_description_list)        

            return render_template('genSong_login.html', audio_generated=True , filename=filename, full_descriptionTH=full_descriptionTH, song_count=song_count)       
        else:
            return render_template('genSong_login.html', audio_generated=False)
    else:
            return render_template('genSong_login.html', audio_generated=False)

@app.route('/save_song/<filename>', methods=['POST'])
def save_song(filename):
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    user_id = session.get('userid')
    file_path = os.path.join('song_files/genSong_files', filename)
    # file_path = session.get('file_path')

    save_directory = os.path.join(app.root_path, 'song_files', 'genSong_files_save')
    new_file_path = os.path.join(save_directory, filename)
    print(new_file_path)
    # Move the file from the original location to the new directory
    shutil.move(file_path, new_file_path)

    if request.method == 'POST' and 'songName' in request.form:
        songName = request.form['songName']
    else:
        songName = filename

    new_file_path = new_file_path.split("\\")[-1]
    file = []
    file.append(new_file_path)
    song_paths_json = json.dumps(file)
    cursor = mysql.connection.cursor()
    insert_query = "INSERT INTO gensong_user (songName, songPath, userID) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (songName, song_paths_json, user_id))
    mysql.connection.commit()
    cursor.close()
    session.pop('file_path', None)
    
    return redirect(url_for('genSong'))

@app.route('/genSongEng', methods=['GET', 'POST'])
def genSongEng():
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    if request.method == 'POST': 

        user_id = session.get('userid')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT COUNT(*) AS song_count FROM gensong_user WHERE userid = %s', (user_id,))
        song_count_result = cursor.fetchone()
        mysql.connection.commit()
        cursor.close()

        song_count = 0

        if song_count_result:
            song_count = song_count_result['song_count'] +1
            print(f'จำนวนเพลงสำหรับผู้ใช้ {user_id} คือ {song_count}')

        descriptions = request.form['descriptions']
        print("description: "+ descriptions)

        full_description = ""  
        emotion_descriptionTH = ""
        song_type_descriptionTH = ""
        musinIns_descriptionTH = ""


        if 'emotion' in request.form :          
            emotion = request.form.getlist('emotion')
            print("emotion: ")
            emotion_str = list_to_str(emotion)
            full_description += emotion_str

            emotion_descriptionTH = emotion_translate(emotion)


        if 'song-type' in request.form :    
            song_type = request.form['song-type']
            # print("song-type: "+ song_type)
            full_description += " " + song_type + " song"
            
            song_type_descriptionTH = songtype_translate(song_type)


        if 'music-instrument' in request.form :   
            music_instruments = request.form.getlist('music-instrument')
            print("music_instruments: ")
            instruments_str = list_to_str_withAnd(music_instruments)
            full_description += " with " + instruments_str

            musinIns_descriptionTH = musinIns_translate(music_instruments)


        full_description += " " + descriptions
        full_descriptionENG = descriptions + musinIns_descriptionTH + emotion_descriptionTH + song_type_descriptionTH


        print("full_description: "+ full_description)

        full_description_list = []
        full_description_list.append(full_description)

        if full_description.strip() != "":
            filename = generateSong(full_description_list)

            return render_template('genSongEng_login.html', audio_generated=True , filename=filename, full_description=full_descriptionENG, song_count=song_count)       
        else:
            return render_template('genSongEng_login.html', audio_generated=False)
    else:
            return render_template('genSongEng_login.html', audio_generated=False)

@app.route('/save_songEng/<filename>', methods=['POST'])
def save_songEng(filename):
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    user_id = session.get('userid')
    file_path = os.path.join('song_files/genSong_files', filename)

    # file_path = session.get('file_path')

    save_directory = os.path.join(app.root_path, 'song_files', 'genSong_files_save')
    new_file_path = os.path.join(save_directory, filename)
    print(new_file_path)
    # Move the file from the original location to the new directory
    shutil.move(file_path, new_file_path)

    if request.method == 'POST' and 'songName' in request.form:
        songName = request.form['songName']
    else:
        songName = filename

    new_file_path = new_file_path.split("\\")[-1]
    file = []
    file.append(new_file_path)
    song_paths_json = json.dumps(file)
    cursor = mysql.connection.cursor()
    insert_query = "INSERT INTO gensong_user (songName, songPath, userID) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (songName, song_paths_json, user_id))
    mysql.connection.commit()
    cursor.close()
    session.pop('file_path', None)
    
    return redirect(url_for('genSongEng'))
    
@app.route('/songLibrary')
def songLibrary():
    if not session.get('userid'):
        return redirect(url_for('login'))

    user_id = session.get('userid')

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM gensong_user WHERE userID = %s', (user_id,))
    songs = cursor.fetchall()
    cursor.close()
    print(songs)
    return render_template('songLibrary_login.html', songs=songs)
        
@app.route('/editSong/<int:song_id>', methods=['GET','POST'])
def editSong(song_id):
    if not session.get('userid'):
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
    song = cursor.fetchone()
    print("song")
    print(song)
    cursor.close()

    print("song path")
    print(song[2])
    song_paths = json.loads(song[2]) if song[2] else []

    if request.method == 'POST' and 'song_name' in request.form and request.form['song_name'].strip() != '':

        song_name = request.form['song_name']

        cursor = mysql.connection.cursor()
        update_stmt = ("UPDATE gensong_user SET songName = %s WHERE songID = %s")
        cursor.execute(update_stmt, (song_name, song_id))
        mysql.connection.commit()
        cursor.close()

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
        song = cursor.fetchone()
        cursor.close()

        return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id)   

    if request.method == 'POST' and 'audio_file' in request.files and request.files['audio_file'].filename != '':

        content_length = request.content_length
        if content_length and content_length > 10 * 1024 * 1024:  # 10 MB
            message = "ขนาดไฟล์ใหญ่เกินไป กรุณาอัปโหลดไฟล์ที่มีขนาดไม่เกิน 10 MB"
            return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id, message=message)
        
        print("len(song_paths)")
        print(len(song_paths))

        if len(song_paths) <= 19:

            audio_file = request.files['audio_file']
            
            unique_filename = str(uuid.uuid4())

            original_filename = audio_file.filename
            file_basename, file_extension = os.path.splitext(original_filename)
            file_extension = file_extension.lower()

            uploaded_file_path = os.path.join('song_files/genSong_files_save', f"{unique_filename}.{file_extension}")

            guide_file_path = os.path.join('song_files/genSong_files_save', f"{unique_filename}.wav")

            if file_extension in ['mp3', 'm4a']:
                audio_file.save(uploaded_file_path)
                
                # Convert to WAV
                audio = AudioSegment.from_file(uploaded_file_path)
                audio.export(guide_file_path, format="wav")
                
                os.remove(uploaded_file_path)
            else:
                audio_file.save(guide_file_path)
                guide_file_path = uploaded_file_path

            filename = unique_filename + ".wav"
            song_paths.append(filename)

            song_paths_json = json.dumps(song_paths)
            cursor = mysql.connection.cursor()
            update_stmt = ("UPDATE gensong_user SET songPath = %s WHERE songID = %s")
            cursor.execute(update_stmt, (song_paths_json, song_id))
            mysql.connection.commit()
            cursor.close()

            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
            song = cursor.fetchone()
            print("new Song")
            print(song)
            cursor.close()
            song_paths = json.loads(song[2]) if song[2] else []

            return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id)
        else:
            message = " คุณอัปโหลดไฟล์เพลงเกินจำนวนที่กำหนดไว้ (สูงสุด 20 ไฟล์เพลง)"
            return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id, message=message)


    if request.method == 'POST' and ('speed' in request.form or 'volume' in request.form):

        song_index = int(request.form['song_index'])
        print("song_index")
        print(song_index)
        old_path = os.path.join('song_files/genSong_files_save', song_paths[song_index])
        # old_path = os.path.join('song_files/genSong_files_save', song[2])
        
        audio = AudioSegment.from_file(old_path)

        if 'speed' in request.form:
            try:
                speed = float(request.form['speed'])
                # Ensure speed is not zero or negative
                if speed <= 0:
                    speed = 1  # Default to normal speed if invalid value is provided
            except ValueError:
                # In case the conversion to float fails
                speed = 1

            # Load the audio data from file
            y, sr = librosa.load(old_path, sr=None)  # Use the actual path to your file

            # Apply time-stretching with librosa
            y_stretched = librosa.effects.time_stretch(y, rate=speed)

            # Convert the numpy array back to an audio file
            y_stretched_int = np.int16(y_stretched/np.max(np.abs(y_stretched)) * 32767)
            audio = AudioSegment(y_stretched_int.tobytes(), frame_rate=sr, sample_width=2, channels=1)

        if 'volume' in request.form:
            # volume_percentage = float(request.form['volume'])

            # if volume_percentage == 100:
            #     dB_change = 0
            # elif volume_percentage > 100:
            #     dB_change = ((volume_percentage - 100) / 100) * 20
            # else:
            #     dB_change = ((volume_percentage - 100) / 100) * 20

            dB_change = float(request.form['volume'])
            print("dB_change",dB_change)

            # Apply volume change with pydub (this is a relative change)
            audio = audio + dB_change  # Note: use "+" to increase and "-" to decrease volume


        filename = secure_filename(f"{uuid.uuid4()}.wav")
        new_path = os.path.join('song_files/genSong_files_save', filename)
        audio.export(new_path, format="wav")

        song_paths[song_index] = filename
        song_paths_json = json.dumps(song_paths)
        cursor = mysql.connection.cursor()
        update_stmt = ("UPDATE gensong_user SET songPath = %s WHERE songID = %s")
        cursor.execute(update_stmt, (song_paths_json, song_id))
        mysql.connection.commit()
        cursor.close()
        # filename = secure_filename(f"{uuid.uuid4()}.wav")
        # new_path = os.path.join('song_files/genSong_files_save', filename)
        # audio.export(new_path, format="wav")
        
        # new_file_path = new_path.split("\\")[-1]
        # cursor = mysql.connection.cursor()
        # update_stmt = ("UPDATE gensong_user SET songPath = %s WHERE songID = %s")
        # cursor.execute(update_stmt, (new_file_path, song_id))
        # mysql.connection.commit()
        # cursor.close()

        if os.path.exists(old_path):
            os.remove(old_path)

        return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id)

    else:
        return render_template('editSong_login.html', song=song, song_paths=song_paths, song_id=song_id)   
      
@app.route('/reload/<int:song_id>', methods=['GET','POST'])
def reload(song_id):
    return redirect(url_for('editSong', song_id=song_id))

@app.route('/chooseFile/<int:song_id>', methods=['GET','POST'])
def chooseFile(song_id):
    if not session.get('userid'):
        return redirect(url_for('login'))
    
    if request.method == 'POST' and 'selectfile' in request.form:
        selectfile = request.form['selectfile']
        print(selectfile)

        user_id = session.get('userid')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM gensong_user WHERE userID = %s', (user_id,))
        songs = cursor.fetchall()
        cursor.close()

        index = int(selectfile)-1
        add_song_paths = songs[index][2]

        add_song_paths_list = json.loads(add_song_paths)

        print("song_paths")
        print(type(add_song_paths_list))

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
        song = cursor.fetchone()
        print(song)
        cursor.close()

        song_paths = json.loads(song[2]) if song[2] else []

        num_song = len(song_paths) + len(add_song_paths_list)

        print("len(song_paths) + len(add_song_paths_list)")
        print(len(song_paths))
        print(len(add_song_paths_list))




        if num_song > 20 :
            message = "คุณอัปโหลดไฟล์เพลงเกินจำนวนที่กำหนดไว้ (สูงสุด 20 ไฟล์เพลง)"
            flash(message)
            return redirect(url_for('editSong', song_id=song_id))
        
        else:
            song_name_list = []
            
            for song_name in add_song_paths_list:
                source_path = os.path.join('song_files/genSong_files_save', song_name)
                
                filename = secure_filename(f"{uuid.uuid4()}.wav")
                destination_path = os.path.join('song_files/genSong_files_save', filename)
                
                shutil.copy(source_path, destination_path)

                song_name_list.append(filename)

                print(f"Copied {source_path} to {destination_path}")

            result = song_paths + song_name_list

            song_paths_json = json.dumps(result)
            cursor = mysql.connection.cursor()
            update_stmt = ("UPDATE gensong_user SET songPath = %s WHERE songID = %s")
            cursor.execute(update_stmt, (song_paths_json, song_id))
            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('editSong', song_id=song_id))

    user_id = session.get('userid')

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM gensong_user WHERE userID = %s', (user_id,))
    songs = cursor.fetchall()
    cursor.close()
    print(songs)
    return render_template('chooseFile.html', songs=songs, song_id=song_id)

# @app.route('/editSong/<int:song_id>', methods=['GET', 'POST'])
# def editSong(song_id):
#     # ตรวจสอบว่าผู้ใช้เข้าสู่ระบบแล้วหรือยัง
#     if not session.get('userid'):
#         return redirect(url_for('login'))

#     # ดึงข้อมูลเพลงจากฐานข้อมูล
#     cursor = mysql.connection.cursor()
#     cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
#     song = cursor.fetchone()
#     print(song)
#     cursor.close()

#     # ถ้าเป็น GET request, แสดงฟอร์มพร้อมข้อมูลเพลงที่มีอยู่
#     if request.method == 'GET':
#         if song:
#             return render_template('editSong_login.html', song=song)
#         else:
#             return 'Song not found', 404
    # change song name
    # elif request.method == 'POST':       
    #     new_song_name = request.form['song_name']
    #     cursor = mysql.connection.cursor()
    #     cursor.execute('UPDATE gensong_user SET songName = %s WHERE songID = %s', (new_song_name, song_id))
    #     mysql.connection.commit()
    #     cursor.close()

    #     return redirect(url_for('songLibrary'))



@app.route('/audio/<filename>')
def send_audio(filename):
    return send_from_directory('song_files/genSong_files_save', filename)

@app.route('/deleteSong/<int:song_id>', methods=['POST'])
def delete_song(song_id):

    if not session.get('userid'):
        print("ไม่มี userid")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_id = session.get('userid')
    try:
        # ดึงข้อมูลจาก body ของคำขอ
        data = request.get_json()
        song_index = data.get('song_index')
        print(song_index)

        cursor = mysql.connection.cursor()
        # ตรวจสอบว่าเพลงเป็นของผู้ใช้นี้หรือไม่
        cursor.execute('SELECT songPath FROM gensong_user WHERE songID = %s AND userID = %s', (song_id, user_id))
        song = cursor.fetchone()
        if song:
            song_path = song[0]
            song_path = json.loads(song_path)
            print(song_path)

            song_name = song_path[song_index]
            print("song_name: "+song_name)

            del song_path[song_index]

            print(song_path)

            # ลบไฟล์เพลงจาก storage
            file_path = os.path.join('song_files/genSong_files_save', song_name)       
            if os.path.exists(file_path):
                os.remove(file_path)
                print("remove from storage")

            # ลบเพลงจากฐานข้อมูล
            song_paths_json = json.dumps(song_path)
            cursor = mysql.connection.cursor()
            update_stmt = ("UPDATE gensong_user SET songPath = %s WHERE songID = %s")
            cursor.execute(update_stmt, (song_paths_json, song_id))
            mysql.connection.commit()
            cursor.close()

            print("ลบเสร็จแล้ว")
            return jsonify({'success': True})
        else:
            print("ไม่พบไฟล์เพลง")
            return jsonify({'success': False, 'message': 'ไม่พบไฟล์เพลง'}), 404
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/deleteWholeSong/<int:song_id>', methods=['POST'])
def deleteWholeSong(song_id):

    print("methoddddd")

    if not session.get('userid'):
        print("ไม่มี userid")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_id = session.get('userid')

    try:
        cursor = mysql.connection.cursor()
        # ตรวจสอบว่าเพลงเป็นของผู้ใช้นี้หรือไม่
        cursor.execute('SELECT songPath FROM gensong_user WHERE songID = %s AND userID = %s', (song_id, user_id))
        song = cursor.fetchone()
        if song:
            song_path = song[0]
            song_path = json.loads(song_path)
            print(song_path)

            cursor = mysql.connection.cursor()
            cursor.execute('DELETE FROM gensong_user WHERE songID = %s', (song_id,))
            mysql.connection.commit()
            cursor.close()
            
            for song_name in song_path:
                file_path = os.path.join('song_files/genSong_files_save', song_name)       
                if os.path.exists(file_path):
                    os.remove(file_path)

            print("ลบเสร็จแล้ว")
            return jsonify({'success': True})
        else:
            print("ไม่พบไฟล์เพลง")
            return jsonify({'success': False, 'message': 'ไม่พบไฟล์เพลง'}), 404
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500
    

@app.route('/downloadSong/<int:song_id>')
def downloadSong(song_id):
    # รับชื่อไฟล์จากฐานข้อมูล (ใช้เป็นตัวอย่าง, ต้องปรับให้เข้ากับการใช้งานจริง)
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM gensong_user WHERE songID = %s', (song_id,))
    song = cursor.fetchone()
    cursor.close()
    if song is None:
        return "Song not found", 404

    song_paths = json.loads(song[2]) if song[2] else []
    combined = AudioSegment.empty()

    for song_path in song_paths:
        path = os.path.join('song_files/genSong_files_save', song_path)
        song_segment = AudioSegment.from_file(path)
        combined += song_segment

    # กำหนดชื่อไฟล์สำหรับเพลงที่รวมแล้ว
    # filename = song[1] + ".wav"
    unique_filename = str(uuid.uuid4())
    filename = unique_filename + ".wav"
    combined_file_path = os.path.join('song_files/genSong_files_save', filename)
    combined.export(combined_file_path, format='wav')

    # ส่งไฟล์เสียงที่รวมแล้วกลับให้ผู้ใช้
    directory = os.path.join(app.root_path, 'song_files/genSong_files_save')

    threading.Thread(target=delete_file_later, args=(combined_file_path, 180)).start()  
    
    return send_from_directory(directory, filename, as_attachment=True)

# @app.route('/deleteSong', methods=['POST'])
# def delete_song():
#     song_index = request.args.get('song_index', type=int)
#     # ดำเนินการลบเพลงจาก `song_paths` และอัปเดตฐานข้อมูล

#     return jsonify({'success': True})

# @app.route('/confirmDelete', methods =['GET', 'POST'])
# def confirmDelete():
#     return render_template('confirmDelete.html', songs=songs, song_id=song_id)
    



if __name__ == "__main__":
    app.run(debug=True)


# @app.route('/genSong', methods=['GET', 'POST'])
# def genSong():
#     if request.method == 'POST':
    
#         def translate_THToENG(descriptions) :
#             os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"googlekey.json"
#             translate_client = translate_v2.Client()
#             text = descriptions
#             target = "en"
#             output = translate_client.translate(text,target_language=target)
#             return output

#         audio_files = []
        
#         descriptionTH = request.form['descriptions']
#         print("descriptionTH: "+ descriptionTH)

#         descriptionENG = translate_THToENG(descriptionTH)
#         print(descriptionENG)

#         descriptions = [descriptionENG['translatedText']]
#         print("descriptions: " + str(descriptions))

#         wav = model.generate(descriptions)

#         # สร้างไบนารีไฟล์เสียง
#         audio_io = io.BytesIO()
#         torchaudio.save(audio_io, format="wav", src=wav[0], sample_rate=model.sample_rate)
#         audio_io.seek(0)
#         audio_data = audio_io.read()

#         # บันทึกไฟล์เสียงลงในฐานข้อมูล
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('INSERT INTO audio_files (file_name, audio_data) VALUES (%s, %s)', ('output.wav', audio_data))
#         mysql.connection.commit()
#         audio_id = cursor.lastrowid
#         cursor.close()

#         return render_template('genSong_login.html', audio_generated=True , audio_id=audio_id)
#     else:
#         return render_template('genSong_login.html', audio_generated=False)