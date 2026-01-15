# -*- coding: utf-8 -*-
"""API Test Script"""
import requests
import json
import uuid

BASE_URL = 'http://localhost:8000'


def test_basic_flow():
    session_id = str(uuid.uuid4())
    print('=== Basic Flow Test ===')
    print('Session ID:', session_id)

    resp = requests.post(BASE_URL + '/api/consultation/start', json={'session_id': session_id})
    data = resp.json()
    print('First question:', data.get('current_question'))

    question_count = 0
    max_questions = 20
    answers = ['yes'] * 5 + ['no'] * 5 + ['unknown'] * 10

    while not data.get('is_complete') and question_count < max_questions:
        question = data.get('current_question')
        if not question:
            break

        answer = answers[question_count] if question_count < len(answers) else 'unknown'
        question_count += 1
        q_display = question[:50] if len(question) > 50 else question
        print('Q' + str(question_count) + ':', q_display, '->', answer)

        resp = requests.post(BASE_URL + '/api/consultation/answer', json={
            'session_id': session_id,
            'answer': answer
        })
        data = resp.json()

    if data.get('is_complete'):
        print('=== Done (' + str(question_count) + ' questions) ===')
        result = data.get('diagnosis_result', {})
        applicable = result.get('applicable_visas', [])
        conditional = result.get('conditional_visas', [])
        print('Applicable:', len(applicable))
        print('Conditional:', len(conditional))


def test_all_yes():
    session_id = 'test_all_yes'
    print('')
    print('=== All YES Test ===')

    resp = requests.post(BASE_URL + '/api/consultation/start', json={'session_id': session_id})
    data = resp.json()

    question_count = 0
    while not data.get('is_complete') and question_count < 30:
        if not data.get('current_question'):
            break
        question_count += 1
        resp = requests.post(BASE_URL + '/api/consultation/answer', json={
            'session_id': session_id,
            'answer': 'yes'
        })
        data = resp.json()

    result = data.get('diagnosis_result', {})
    applicable = [v.get('visa') for v in result.get('applicable_visas', [])]
    print('Questions:', question_count)
    print('Applicable:', applicable)


def test_all_no():
    session_id = 'test_all_no'
    print('')
    print('=== All NO Test ===')

    resp = requests.post(BASE_URL + '/api/consultation/start', json={'session_id': session_id})
    data = resp.json()

    question_count = 0
    while not data.get('is_complete') and question_count < 30:
        if not data.get('current_question'):
            break
        question_count += 1
        resp = requests.post(BASE_URL + '/api/consultation/answer', json={
            'session_id': session_id,
            'answer': 'no'
        })
        data = resp.json()

    result = data.get('diagnosis_result', {})
    applicable = [v.get('visa') for v in result.get('applicable_visas', [])]
    print('Questions:', question_count)
    print('Applicable:', applicable)


def test_all_unknown():
    session_id = 'test_all_unknown'
    print('')
    print('=== All UNKNOWN Test ===')

    resp = requests.post(BASE_URL + '/api/consultation/start', json={'session_id': session_id})
    data = resp.json()

    question_count = 0
    while not data.get('is_complete') and question_count < 30:
        if not data.get('current_question'):
            break
        question_count += 1
        resp = requests.post(BASE_URL + '/api/consultation/answer', json={
            'session_id': session_id,
            'answer': 'unknown'
        })
        data = resp.json()

    result = data.get('diagnosis_result', {})
    applicable = [v.get('visa') for v in result.get('applicable_visas', [])]
    conditional = [v.get('visa') for v in result.get('conditional_visas', [])]
    print('Questions:', question_count)
    print('Applicable:', applicable)
    print('Conditional:', conditional)


def test_back_functionality():
    session_id = 'test_back'
    print('')
    print('=== Back Function Test ===')

    resp = requests.post(BASE_URL + '/api/consultation/start', json={'session_id': session_id})
    data = resp.json()

    for i in range(3):
        if not data.get('current_question'):
            break
        q = data.get('current_question')
        q_display = q[:40] if len(q) > 40 else q
        print('Q' + str(i+1) + ':', q_display)
        resp = requests.post(BASE_URL + '/api/consultation/answer', json={
            'session_id': session_id,
            'answer': 'yes'
        })
        data = resp.json()

    current_q = data.get('current_question')
    if current_q:
        print('Current:', current_q[:40])

    resp = requests.post(BASE_URL + '/api/consultation/back', json={
        'session_id': session_id,
        'steps': 1
    })
    data = resp.json()
    after_back = data.get('current_question')
    if after_back:
        print('After back:', after_back[:40])


if __name__ == '__main__':
    try:
        resp = requests.get(BASE_URL + '/api/health')
        print('API Status:', resp.json().get('status'))
        print('')

        test_basic_flow()
        test_all_yes()
        test_all_no()
        test_all_unknown()
        test_back_functionality()

        print('')
        print('=== All Tests Done ===')
    except requests.exceptions.ConnectionError:
        print('[ERROR] Cannot connect to:', BASE_URL)
        print('Make sure the server is running')
