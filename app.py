import os
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS
import json
import gradio as gr
import time
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client_llm = Groq(api_key=api_key)

import time

def cari_web(query):
    try:
        hasil = DDGS().text(query, max_results=3)
        if not hasil:
            return "Tidak ditemukan hasil pencarian."
        ringkasan = ""
        for r in hasil:
            ringkasan += f"Judul: {r['title']}\nRingkasan: {r['body']}\nSumber: {r['href']}\n\n"
        return ringkasan
    except Exception as e:
        return f"Pencarian web gagal (masalah koneksi): {str(e)}"


def agent_peneliti(topik, max_langkah=5):
    system_prompt = """Kamu adalah seorang peneliti. Tugasmu HANYA mengumpulkan fakta-fakta 
penting tentang topik yang diberikan menggunakan tool pencarian web. 
Kumpulkan minimal 3-5 poin fakta. Jangan menyusun artikel, cukup daftar fakta mentah."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Kumpulkan fakta-fakta tentang: {topik}"}
    ]

    for i in range(max_langkah):
        try:
            response = client_llm.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            print(f"Percobaan {i+1} gagal ({str(e)}), mencoba lagi...")
            time.sleep(1)
            continue  # coba lagi dari awal loop, tanpa menghentikan seluruh proses

        pesan = response.choices[0].message

        if not pesan.tool_calls:
            return pesan.content

        messages.append(pesan)
        for tool_call in pesan.tool_calls:
            argumen = json.loads(tool_call.function.arguments)
            nama_tool = tool_call.function.name

            if nama_tool not in daftar_fungsi:
                hasil = f"Tool '{nama_tool}' tidak tersedia."
            else:
                hasil = daftar_fungsi[nama_tool](**argumen)

            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(hasil)})

    return "Gagal mengumpulkan fakta setelah beberapa percobaan."
def agent_penulis(topik, fakta_fakta):
    system_prompt = """Kamu adalah seorang penulis profesional.Tugasmu menyusun fakta fakta
    yang diberikan menjadi sebuah ringkasan yang mengalir, enak dibaca, dan terstruktur rapi
    dengan paragraf pembuka,isi, dan penutup.Gunakan bahasa indonesia yang baik. """
    prompt_user = f"""Topik: {topik}

Fakta-fakta hasil riset:
{fakta_fakta}

Susun menjadi ringkasan artikel yang rapi."""

    response = client_llm.chat.completions.create(
        model = "openai/gpt-oss-20b",
        messages=[
            {'role' : "system", 'content': system_prompt},
            {'role' : 'user' , 'content' : prompt_user}
        ]
        
    )
    return response.choices[0].message.content
def proses_multi_agent(topik):
    fakta = agent_peneliti(topik)
    artikel = agent_penulis(topik, fakta)
    return artikel 

demo = gr.Interface(
    fn = proses_multi_agent,
    inputs = gr.Textbox(label="Topik Artikel", placeholder="Misal: perkembangan AI terbaru tahun 2026"),
    outputs=gr.Textbox(label="Artikel Hasil Multi-Agent", lines=15),
    title="Multi-Agent: Peneliti & Penulis",
    description="Masukkan topik, Agent Peneliti akan mencari fakta dari internet, lalu Agent Penulis akan menyusunnya jadi artikel rapi.",
    examples=[
        "perkembangan AI terbaru tahun 2026",
        "manfaat olahraga pagi bagi kesehatan",
        "tren teknologi energi terbarukan"
    ]
)

demo.launch(share=True)


