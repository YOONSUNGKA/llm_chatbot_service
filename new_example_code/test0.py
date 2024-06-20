import os
import logging
import threading
import simpleaudio as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gtts import gTTS
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import speech_recognition as sr
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
import googleapiclient.discovery
from pytube import YouTube
import io
from io import BytesIO
import csv
import time

# FastAPI 초기 설정
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI 엔드포인트
class VoiceCommandRequest(BaseModel):
    userId: str
    userAgent: str
    carCode: str
    dttm: str
    query: str

# 1. 환경변수 설정
# API Key 호출
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
# Youtube Data API 클라이언트 생성
youtube = googleapiclient.discovery.build("youtube", "v3",
                                          developerKey=os.getenv("GOOGLE_API_KEY"))
# 로그설정
log_directory = "../log/"
log_filename = "query_log.txt"
log_path = os.path.join(log_directory, log_filename)

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(filename=log_path,
                    level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    filemode='a')

def log_query_and_response(query, response):
    logging.info(f"Query: {query}")
    logging.info(f"Response: {response}")

# 차임음 설정
ping_sound_path = "../sounds/ping-82822.mp3"
ding_sound_path = "../sounds/ding-36029.mp3"

def play_sound(sound_path):
    playsound(sound_path)

# csv 파일 설정
def extract_csv_content(csv_path, specific_columns=None):
    csv_content = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if specific_columns:
                selected_columns = {col: row[col] for col in specific_columns if col in row}
                csv_content.append(selected_columns)
            else:
                csv_content.append(row)
    return csv_content

def get_car_list():
    car_csv_path = os.path.join('../csvs/', 'car_info_list.csv')
    car_list = extract_csv_content(car_csv_path, specific_columns=['filename'])
    car_list = [row['filename'] for row in car_list]  # filename 컬럼만 추출하여 리스트로 변환
    #print(f"Car list: {car_list}")
    return car_list

def get_restaurant_list():
    restaurant_csv_path = os.path.join('../csvs/', 'seongsu_restaurant_final.csv')
    specific_columns = ['title', 'local_category', 'food_category_1st', 'food_category_2nd', 'dining_food_cate_1', 
                        'dining_food_cate_2', 'information', 'isParking', 'isValet', 'isPet', 'isPackaging', 
                        'isReservation', 'address', 'telephone', 'menu1', 'price1', 'menu2', 'price2', 
                        'menu URL', 'diningcode_Star', 'diningcode_Score', 'comment', 'comment_weight', 'rank_score',
                        'mon_business', 'mon_breaktime', 'tues_business', 'tues_breaktime', 'wed_business', 
                        'wed_breaktime', 'thurs_business', 'thurs_breaktime', 'fri_business', 'fri_breaktime', 
                        'sat_business', 'sat_breaktime', 'sun_business', 'sun_breaktime', 'latitude', 'longitude', 
                        'img_file1', 'img_file2', 'closest_parking_name', 'closest_parking_address', 
                        'closest_parking_latitude', 'closest_parking_longitude']
    restaurant_list = extract_csv_content(restaurant_csv_path, specific_columns=specific_columns)
    #print(f"Restaurant list: {restaurant_list}")
    return restaurant_list

#2. OPEN AI API 체이닝
car_list = get_car_list()
car_list_str = ', '.join(car_list)

restaurant_list = get_restaurant_list()
restaurant_titles = [restaurant['title'] for restaurant in restaurant_list]
restaurant_list_str = ', '.join(restaurant_titles)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "안녕하세요! 저는 드라이브톡입니다."
               "차량에 대한 사용자 정보, 음악 재생, 성수동 맛집 정보를 정확히 제공해드릴 수 있는 시스템입니다."
               f"현재 데이터베이스에 '{car_list_str}' 차량 정보가 있으며, 성수동 맛집 정보도 제공해드립니다."
               f"현재 데이터베이스에 '{restaurant_list_str}' 성수동 맛집 정보가 있습니다."
               "상세한 설명을 요청하셔도 답변은 250자 이내로 간결하게 드립니다."
               "사람과 대화하듯 편하게 구어체로 답변해 주되 존댓말로 답변해 주세요."
               ),
    ("user", "{user_input}"),
])

llm = ChatOpenAI(model_name="gpt-4o",temperature=0, max_tokens=2048)

chain = LLMChain(llm=llm, prompt=chat_prompt, output_key='result')

# 텍스트 처리
def convert_text(text):
    text = text.replace("L", "리터")
    text = text.replace("kg.m", "킬로그램퍼미터")
    text = text.replace("cc", "씨씨")
    text = text.replace("kg", "킬로그램")
    text = text.replace("km", "킬로미터")
    text = text.replace("rpm", "알피엠")
    text = text.replace("nm", "알피엠")
    text = text.replace("Nm", "뉴턴미터")
    return text

def text_to_speech(text, output_file_path=None, lang='ko'):
    cleaned_text = text.replace('*', '').replace('**', '')
    cleaned_text = convert_text(cleaned_text)
    tts = gTTS(text=cleaned_text, lang=lang)
    
    if output_file_path:
        tts.save(output_file_path)
        playsound(output_file_path)
    else:
        # output_file_path가 None이면 메모리에서 바로 재생
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio = AudioSegment.from_file(audio_fp, format="mp3")
        play(audio)

# 4. 응답 및 쿼리 처리
def process_llm_response(llm_response, query):
    cleaned_response = ""
    if isinstance(llm_response, str):
        cleaned_response = llm_response.replace('*', '').replace('**', '')
        cleaned_response = convert_text(cleaned_response)
        print(cleaned_response)  # 터미널에 출력
        if "틀어 줘" in query or "재생" in query:
            keyword = llm_response.split(" ")[0]
            return play_music_request(keyword)
    else:
        cleaned_response = llm_response.get("result", "").replace('*', '').replace('**', '')
        cleaned_response = convert_text(cleaned_response)
        print(cleaned_response)  # 터미널에 출력
        print('\n\nSources:')
        for source in llm_response.get("source_documents", []):
            print(source.metadata.get('source', 'Unknown'))
    return cleaned_response

def shorten_text(text, max_length=1000):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def query_and_summarize(query):
    short_query = shorten_text(query)
    inputs = {"user_input": short_query}
    llm_response = chain.invoke(inputs)
    time.sleep(2)  # 2초 대기
    cleaned_response = process_llm_response(llm_response, query)
    log_query_and_response(query, cleaned_response)
    return cleaned_response

# 5. 음악 검색 및 재생
music_thread = None
stop_event = threading.Event()

def search_music(keyword):
    search_response = youtube.search().list(
        q=keyword,
        part="id",
        type="video",
        maxResults=1
    ).execute()
    
    video_id = search_response["items"][0]["id"]["videoId"]
    return video_id

def download_audio(video_id):
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            raise Exception("No audio stream available")
        audio_data = io.BytesIO()
        stream.stream_to_buffer(audio_data)
        audio_data.seek(0)
        return audio_data, None
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None, str(e)

def play_music_thread(audio_data):
    try:
        if not audio_data:
            print("No audio data to play")
            return
        audio = AudioSegment.from_file(audio_data)
        stop_event.clear()
        play_obj = sa.play_buffer(audio.raw_data, num_channels=audio.channels, bytes_per_sample=audio.sample_width, sample_rate=audio.frame_rate)
        while play_obj.is_playing():
            if stop_event.is_set():
                play_obj.stop()
                break
    except Exception as e:
        print(f"Error playing audio: {e}")

def play_music_request(keyword):
    try:
        video_id = search_music(keyword)
        audio_data, error = download_audio(video_id)
        if audio_data:
            response_text = f"'{keyword}'을(를) 검색할게요."
            print(response_text)
            # 음성 출력을 먼저 수행
            text_to_speech(response_text, None)
            # 음성 출력이 완료된 후에 음악 재생 시작
            global music_thread
            music_thread = threading.Thread(target=play_music_thread, args=(audio_data,))
            music_thread.start()
            return response_text
        else:
            response_text = f"'{keyword}'을(를) 재생할 수 없습니다. 오류: {error}"
            print(response_text)
            # 오류 메시지를 음성으로 출력
            text_to_speech(response_text, None)
            return response_text
    except Exception as e:
        response_text = f"음악을 재생하는 중에 문제가 발생했습니다. 다시 시도해주세요. 오류: {str(e)}"
        print(response_text)
        # 오류 메시지를 음성으로 출력
        text_to_speech(response_text, None)
        return response_text

def stop_music():
    global stop_event, music_thread
    if music_thread and music_thread.is_alive():
        stop_event.set()
        music_thread.join()
        print("음악 재생을 중지했습니다.")
    else:
        print("현재 재생 중인 음악이 없습니다.")

# 6. 음성 인식 및 처리
recognizer = sr.Recognizer()

def listen_and_process():
    try:
        with sr.Microphone() as source:
            print("주변 소음 수준 조정 중...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("소음 조정 완료")

            print("네, 말씀하세요...")
            text_to_speech("네, 말씀하세요")
            play_sound(ping_sound_path)
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("음성 인식 중...")
            text = recognizer.recognize_google(audio_data, language='ko-KR')
            print("인식된 텍스트: " + text)
            play_sound(ding_sound_path)
            
            music_synonyms = ["음악 재생", "틀어 줘", "틀어줘", "들려줘", "들려 줘", "플레이 해줘", "재생 해줘"]
            restaurant_synonyms = ["맛집 추천", "맛집 알려줘", "맛집 추천해 줘", "맛집 알려 줘", "추천", "맛집", "식당",
                                   "양식", "한식", "카페", "중식", "일식", "아시안", "술집",
                                   "햄버거", "백반", "파스타", "곰탕", "베이커리", "카페", "케이크", "우육면", "커피", 
                                   "소바", "오므라이스", "베이글", "족발", "닭요리", "돈카츠", "일정식", "솥밥", "디저트", 
                                   "우동", "와인바", "국수", "카레", "쌀국수", "고깃집", "보쌈", "샐러드", "초밥", 
                                   "피자", "브런치", "중식당", "칵테일", "맥주", "딤섬", "막걸리", "삼겹살", 
                                   "오코노미야끼", "치킨", "부대찌개", "태국", "짜장면", "양꼬치", "해물", "회", 
                                   "순대", "냉면", "분식", "규카츠", "오마카세", "라멘", "마라탕", "짬뽕", 
                                   "샌드위치", "김밥", "소시지", "국밥", "샤브샤브", "스테이크", "타코", "아시안요리", 
                                   "에스프레소", "아이스크림", "갈비", "곱창", "비건"]
            
            if any(synonym in text for synonym in music_synonyms):
                for synonym in music_synonyms:
                    if synonym in text:
                        keyword = text.replace(synonym, "").strip()
                        response_text = play_music_request(keyword)
                        return {
                            "success": True,
                            "answerType": "music",
                            "answer": keyword
                        }
            
            elif any(synonym in text for synonym in restaurant_synonyms):
                for synonym in restaurant_synonyms:
                    if synonym in text:
                        keyword = text.replace(synonym, "").strip()
                        response_text = query_and_summarize(text)
                        text_to_speech(response_text)
                        return {
                            "success": True,
                            "answerType": "restaurant",
                            "answer": response_text
                        }
            
            else:
                response_text = query_and_summarize(text)
                # TTS 기능으로 음성 출력만 하고 mp3 파일로 저장하지 않음
                text_to_speech(response_text)
                return {
                    "success": True,
                    "answerType": "vehicle",
                    "answer": response_text
                }
    except sr.WaitTimeoutError:
        return {
            "success": False,
            "answerType": "error",
            "answer": "음성 인식 시간 초과"
        }
    except Exception as e:
        return {
            "success": False,
            "answerType": "error",
            "answer": f"음성 인식 중 오류가 발생했습니다: {e}"
        }

@app.post("/listen")
async def listen_endpoint(request: VoiceCommandRequest):
    response = listen_and_process()
    return response

@app.post("/stop_music")
async def stop_music_endpoint():
    stop_music()
    return {"response": "음악 재생을 중지했습니다."}

# FastAPI 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)