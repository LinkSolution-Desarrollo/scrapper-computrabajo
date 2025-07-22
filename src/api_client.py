# -*- coding: utf-8 -*-
import requests
from src import config

def send_vacante(data_vacante):
    try:
        r = requests.post(config.WEBHOOK_VACANT, json=data_vacante, timeout=10)
        print(f"API Vacante: {' Enviada' if r.status_code == 200 else f' Error {r.status_code}: {r.text}'}")
    except Exception as e:
        print(f" Error al enviar vacante a API: {e}")

def send_candidato(data_candidato):
    try:
        r_cand = requests.post(config.WEBHOOK_INSERT, json=data_candidato, timeout=10)
        print(f"API Candidato: {' Enviado' if r_cand.status_code == 200 else f' Error {r_cand.status_code}: {r_cand.text}'}")
    except Exception as e_http_cand:
        print(f" Error HTTP al enviar candidato: {e_http_cand}")
