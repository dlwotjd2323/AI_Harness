import os
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# 1. 구형 PC(두뇌 서버) 연결 설정 (IP 변경 필수!)
os.environ["OPENAI_API_BASE"] = "YOUR_TOKEN"
os.environ["OPENAI_API_KEY"] = "lm-studio" # 형식상의 키

# LLM 뇌 연결
llm = ChatOpenAI(model="local-model", temperature=0.7)

print("🚀 1인 기업 하네스 시스템 가동 중...\n")

# 2. 에이전트 생성 (직원 고용)
developer = Agent(
    role='시니어 파이썬 개발자',
    goal='주어진 요구사항에 맞춰 오류 없는 완벽한 파이썬 코드를 작성합니다.',
    backstory='당신은 1인 기업의 핵심 개발자입니다. 항상 코드를 짧고 명확하게 작성하며 한국어로 친절하게 설명합니다.',
    verbose=True,
    allow_delegation=False,
    llm=llm
)

qa_engineer = Agent(
    role='수석 품질 보증(QA) 엔지니어',
    goal='개발자가 작성한 코드를 꼼꼼히 리뷰하고 개선점을 찾습니다.',
    backstory='당신은 버그를 절대 용납하지 않는 깐깐한 검수자입니다. 코드의 효율성과 안전성을 한국어로 평가합니다.',
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 3. 작업(Task) 지시
task1_code = Task(
    description='1부터 100까지 짝수만 골라서 더하는 파이썬 코드를 작성하세요.',
    expected_output='1부터 100까지 짝수의 합을 구하는 파이썬 코드와 짧은 설명',
    agent=developer
)

task2_review = Task(
    description='작성된 코드를 리뷰하고, 더 나은 방법(예: 수학 공식 사용)이 있다면 제안하세요.',
    expected_output='코드에 대한 리뷰 결과 및 개선된 코드 제안',
    agent=qa_engineer
)

# 4. 팀 구성 및 실행 (Crew)
company = Crew(
    agents=[developer, qa_engineer],
    tasks=[task1_code, task2_review],
    verbose=True
)

print("👨‍💻 직원들이 작업을 시작했습니다. 터미널의 진행 상황을 지켜보세요...\n")
result = company.kickoff()

print("\n================================================")
print("🎯 [최종 작업 결과물]:\n")
print(result)
print("================================================")