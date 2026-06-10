import streamlit as st
import random

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="망각곡선 기반 IT 용어 학습기", page_icon="🧠", layout="centered")

# --- 2. 세션 상태(Session State) 초기화 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'setup'          # 'setup', 'quiz', 'feedback', 'report'
    st.session_state.quiz_data = {}
    st.session_state.quiz_pool = []
    st.session_state.total_questions = 0
    st.session_state.correct_count = 0
    
    st.session_state.current_question = ""
    st.session_state.current_q_num = 1
    
    # 피드백 화면을 위한 상태 변수
    st.session_state.last_user_ans = ""
    st.session_state.last_result = ""        # 'correct' 또는 'wrong'
    
    # 누적 오답 저장 (서버 배포 환경에서도 안전하도록 세션에 저장)
    if 'wrong_answers' not in st.session_state:
        st.session_state.wrong_answers = {}   # { 단어: [뜻, 틀린횟수] }
        
    st.session_state.log = ["🤖 지능형 오답 추적 시스템이 가동되었습니다."]

# --- 3. 사이드바 (Sidebar) 오답 횟수 추적 UI ---
with st.sidebar:
    st.header("📝 지능형 누적 오답 노트")
    st.caption("자주 틀린 취약한 단어를 먼저 보여줍니다.")
    
    if st.session_state.wrong_answers:
        # 틀린 횟수가 많은 순서대로 정렬
        sorted_terms = sorted(
            st.session_state.wrong_answers.keys(), 
            key=lambda k: st.session_state.wrong_answers[k][1], 
            reverse=True
        )
        
        display_text = ""
        download_text = "" # TXT 파일 저장용 텍스트
        
        for term in sorted_terms:
            definition, count = st.session_state.wrong_answers[term]
            
            # 1) 화면 표시용 텍스트 (이모지 포함)
            if count >= 3:
                display_text += f"🚨 [{count}회 오답] {term} : {definition}\n"
            elif count == 2:
                display_text += f"🔴 [{count}회 오답] {term} : {definition}\n"
            else:
                display_text += f"🟠 [{count}회 오답] {term} : {definition}\n"
                
            # 2) 파일 다운로드용 텍스트 (나중에 다시 재입력 단어장으로 쓸 수 있게 깔끔하게 저장)
            download_text += f"{term} : {definition}\n"
                
        st.text_area("나의 취약점 분석", value=display_text, height=350, disabled=True)
        
        # --- [방법 1 적용] 파일 다운로드 버튼 ---
        st.download_button(
            label="💾 바탕화면에 오답 노트 다운로드",
            data=download_text,
            file_name="wrong_answers.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        if st.button("🗑️ 오답 노트 싹 지우기", use_container_width=True):
            st.session_state.wrong_answers = {}
            st.rerun()
    else:
        st.info("아직 누적된 오답이 없습니다. 완벽하네요!")


# --- 4. 메인 화면 구성 ---

# [화면 1] 단어장 입력 화면
if st.session_state.stage == 'setup':
    st.title("📚 나만의 단어장 설정")
    st.write("단어와 뜻을 콜론( : )으로 구분하여 한 줄에 하나씩 적어주세요.")
    
    default_text = """CPU : 중앙처리장치
레지스터 : CPU 내부의 고속 소형 메모리
캐시메모리 : CPU와 RAM 사이의 속도 차이를 줄여주는 고속 메모리
RAM : 컴퓨터의 주기억장치
스택 : 후입선출(LIFO) 구조의 자료구조
큐 : 선입선출(FIFO) 구조의 자료구조"""
    
    user_input = st.text_area("데이터 입력", value=default_text, height=200)
    
    if st.button("🚀 이 데이터로 퀴즈 시작하기", use_container_width=True):
        lines = user_input.strip().split('\n')
        quiz_data = {}
        error_found = False
        
        for line in lines:
            if not line.strip(): continue
            if ":" in line:
                term, definition = line.split(":", 1)
                quiz_data[term.strip()] = definition.strip()
            else:
                st.error(f"다음 줄의 형식이 잘못되었습니다 (콜론 필요):\n{line}")
                error_found = True
                break
        
        if not error_found:
            if len(quiz_data) > 0:
                st.session_state.quiz_data = quiz_data
                st.session_state.quiz_pool = list(quiz_data.keys())
                random.shuffle(st.session_state.quiz_pool)
                st.session_state.total_questions = len(st.session_state.quiz_pool)
                st.session_state.current_q_num = 1
                st.session_state.correct_count = 0
                st.session_state.current_question = st.session_state.quiz_pool.pop(0)
                st.session_state.stage = 'quiz'
                st.rerun()
            else:
                st.error("최소 1개 이상의 단어를 입력해주세요.")

# [화면 2] 퀴즈 출제 화면 (정답 입력받는 곳)
elif st.session_state.stage == 'quiz':
    st.title("🧠 망각곡선 지능형 퀴즈")
    st.caption("뇌가 단어를 잊어버릴 때쯤 시스템이 기습 복습을 보냅니다.")
    
    progress_val = st.session_state.current_q_num / st.session_state.total_questions
    st.progress(progress_val)
    st.write(f"**진행도:** {st.session_state.current_q_num} / {st.session_state.total_questions}")
    
    st.info(f"문제: 다음 용어의 알맞은 뜻은?\n### 👉 [ {st.session_state.current_question} ]")
    
    user_ans = st.text_input("💡 정답 입력 (뜻을 정확히 적으세요):", key="quiz_input")
    
    if st.button("정답 제출하기", use_container_width=True):
        if not user_ans.strip():
            st.warning("정답을 입력해주세요!")
        else:
            correct_ans = st.session_state.quiz_data[st.session_state.current_question]
            user_ans_processed = user_ans.replace(" ", "").strip()
            correct_ans_processed = correct_ans.replace(" ", "")
            
            st.session_state.last_user_ans = user_ans.strip()
            
            if user_ans_processed == correct_ans_processed:
                st.session_state.correct_count += 1
                st.session_state.log.append(f"✅ 정답: '{st.session_state.current_question}'을(를) 맞혔습니다.")
                st.session_state.last_result = 'correct'
            else:
                st.session_state.log.append(f"❌ 오답: '{st.session_state.current_question}' 틀림. (입력: {user_ans.strip()})")
                st.session_state.last_result = 'wrong'
                
                # 오답노트 데이터 갱신
                term = st.session_state.current_question
                if term in st.session_state.wrong_answers:
                    st.session_state.wrong_answers[term][1] += 1
                else:
                    st.session_state.wrong_answers[term] = [correct_ans, 1]
            
            # 제출 후 피드백 단계로 화면 전환
            st.session_state.stage = 'feedback'
            st.rerun()

    st.divider()
    st.write("📊 **실시간 시스템 분석 로그:**")
    for log_msg in reversed(st.session_state.log[-5:]):
        st.text(log_msg)

# [화면 3] 정답/오답 결과 피드백 및 기습 복습 화면
elif st.session_state.stage == 'feedback':
    st.title("🧠 망각곡선 지능형 퀴즈")
    
    current_word = st.session_state.current_question
    correct_ans = st.session_state.quiz_data[current_word]
    
    # 1. 방금 푼 문제에 대한 결과 피드백
    if st.session_state.last_result == 'correct':
        st.success(f"🎉 훌륭합니다! **[{current_word}]** 정답입니다.")
        st.write(f"내가 입력한 답: `{st.session_state.last_user_ans}`")
        
        if st.button("다음 문제로 이동 ➡️", use_container_width=True):
            if len(st.session_state.quiz_pool) > 0:
                st.session_state.current_q_num += 1
                st.session_state.current_question = st.session_state.quiz_pool.pop(0)
                st.session_state.stage = 'quiz'
            else:
                st.session_state.stage = 'report'
            st.rerun()
            
    else:
        # 2. 틀렸을 때 -> 화면에서 즉시 '기습 복습(재입력)' 유도
        st.error(f"❌ 틀렸습니다! **[{current_word}]**의 정답은 **[{correct_ans}]** 입니다.")
        st.write(f"내가 입력한 답: `{st.session_state.last_user_ans}`")
        
        st.warning("⚠️ [기습 복습] 뇌가 단어를 완전히 망각하기 전에 정답을 다시 한번 타이핑하며 각인하세요!")
        
        # 기습 복습 정답 재입력 칸
        review_ans = st.text_input("👉 위 정답을 똑같이 입력해보세요:", key="review_input")
        
        if st.button("복습 완료 및 다음 문제로 ➡️", use_container_width=True):
            if not review_ans.strip():
                st.error("복습 정답을 입력해야 다음 문제로 넘어갈 수 있습니다.")
            else:
                review_ans_processed = review_ans.replace(" ", "").strip()
                correct_ans_processed = correct_ans.replace(" ", "")
                
                if review_ans_processed == correct_ans_processed:
                    st.session_state.log.append(f"🧠 [기억 복구 완료] '{current_word}' 재복습 성공!")
                else:
                    st.session_state.log.append(f"📉 [망각 심화] '{current_word}' 재복습 타이핑 실패.")
                
                if len(st.session_state.quiz_pool) > 0:
                    st.session_state.current_q_num += 1
                    st.session_state.current_question = st.session_state.quiz_pool.pop(0)
                    st.session_state.stage = 'quiz'
                else:
                    st.session_state.stage = 'report'
                st.rerun()

    st.divider()
    st.write("📊 **실시간 시스템 분석 로그:**")
    for log_msg in reversed(st.session_state.log[-5:]):
        st.text(log_msg)

# [화면 4] 최종 리포트 화면
elif st.session_state.stage == 'report':
    st.title("🎉 모든 테스트가 종료되었습니다!")
    
    score_percent = int((st.session_state.correct_count / st.session_state.total_questions) * 100) if st.session_state.total_questions > 0 else 0
    
    st.metric(label="당신의 암기 지수", value=f"{score_percent}%")
    
    if score_percent >= 80:
        st.success("👉 진단 결과: 단기 기억력이 매우 우수합니다. 내일 오전 11시에 최종 복습을 권장합니다.")
    elif score_percent >= 50:
        st.warning("👉 진단 결과: 평범한 망각 주기를 보입니다. 오늘 저녁 9시에 오답 노트를 정독하세요.")
    else:
        st.error("👉 진단 결과: 망각 속도가 매우 빠릅니다! 1시간 뒤 재시험을 보는 것을 강력 추천합니다.")
        
    if st.button("🔄 처음으로 돌아가기", use_container_width=True):
        # 오답 노트를 제외한 퀴즈 상태만 초기화
        saved_wrong = st.session_state.wrong_answers
        st.session_state.clear()
        st.session_state.wrong_answers = saved_wrong
        st.session_state.stage = 'setup'
        st.rerun()
