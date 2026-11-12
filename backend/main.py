import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Pastikan path direktori backend terdaftar di sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import billing
import chatbot_engine
import database

app = FastAPI(
    title="Chatbot Backend API",
    description="Backend API untuk Sistem Chatbot Layanan Digital",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    server: str
    database: str


class HealthErrorResponse(BaseModel):
    status: str
    server: str
    database: str
    details: str


class BillingValidResponse(BaseModel):
    total_payment: int
    total_outstanding_balance: int
    valid: bool = True


class BillingInvalidResponse(BaseModel):
    valid: bool = False
    invoice_no: str


class ClientLoginRequest(BaseModel):
    client_id: str
    password: Optional[str] = ""


class ClientResponse(BaseModel):
    client_id: str
    client_name: str
    company_name: Optional[str] = None
    phone_number: str
    official_domain: Optional[str] = None
    created_at: Optional[str] = None


class InvoiceResponse(BaseModel):
    invoice_no: str
    client_id: str
    service_type: str
    package_name: str
    total_amount: int
    amount_paid: int
    payment_status: str
    due_date: Optional[str] = None
    outstanding_balance: int = 0


class KnowledgeBaseResponse(BaseModel):
    id: int
    category: str
    keyword_triggers: str
    title: str
    content: str


class KnowledgeBaseCreateRequest(BaseModel):
    category: str
    keyword_triggers: str
    title: str
    content: str


class ConversationResponse(BaseModel):
    conversation_id: str
    client_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    total_messages: int = 0
    messages: List["ChatMessageResponse"] = []


class ChatRequest(BaseModel):
    client_id: str
    conversation_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    client_id: str
    response: str
    turn_index: int
    detected_intent: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: str
    turn_index: int
    sender: str
    message_text: str
    detected_intent: Optional[str] = None
    created_at: Optional[str] = None


@app.get(
    "/health",
    summary="Memeriksa status server dan database",
    description="Endpoint untuk memeriksa kesehatan server dan koneksi database SQLite.",
    response_model=HealthResponse,
    responses={
        200: {
            "model": HealthResponse,
            "description": "Server dan database berfungsi normal",
        },
        503: {
            "model": HealthErrorResponse,
            "description": "Koneksi database bermasalah",
        },
    },
)
def health_check():
    db_ok, db_status = database.check_db_health()

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "server": "running",
                "database": "disconnected",
                "details": db_status,
            },
        )

    return {
        "status": "healthy",
        "server": "running",
        "database": db_status,
    }


@app.get(
    "/billing/{client_id}",
    summary="Mengambil informasi tagihan klien",
    description="Mengambil informasi tagihan klien dan memeriksa konsistensi status pembayaran dengan nominal tagihan.",
    response_model=Union[BillingValidResponse, BillingInvalidResponse],
    responses={
        200: {
            "description": "Informasi tagihan berhasil diproses (valid atau terdeteksi inkonsistensi)",
        },
        404: {
            "description": "Klien atau invoice tidak ditemukan",
        },
    },
)
def get_billing_info(client_id: str):
    client_exists, invoices = database.get_client_and_invoices(client_id)

    if not client_exists and not invoices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' tidak ditemukan",
        )

    if not invoices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice untuk client '{client_id}' tidak ditemukan",
        )

    return billing.process_client_billing(invoices)


@app.post(
    "/auth/login",
    summary="Autentikasi client",
    description="Validasi keberadaan client_id pada tabel clients tanpa validasi password.",
)
def login(req: ClientLoginRequest):
    client_id = req.client_id.strip() if req.client_id else ""
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID wajib diisi",
        )

    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client ID '{client_id}' tidak ditemukan di tabel clients",
        )

    return {
        "success": True,
        "message": "Login berhasil",
        "client": client,
    }


@app.get(
    "/clients",
    summary="Daftar semua clients",
    description="Mengambil seluruh daftar client dari tabel clients.",
    response_model=List[ClientResponse],
)
def get_clients():
    return database.get_all_clients()


@app.get(
    "/clients/{client_id}",
    summary="Detail client",
    description="Mengambil detail client berdasarkan client_id.",
    response_model=ClientResponse,
)
def get_client(client_id: str):
    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' tidak ditemukan",
        )
    return client


@app.get(
    "/clients/{client_id}/invoices",
    summary="Daftar invoice client",
    description="Mengambil seluruh invoice milik client tertentu dari tabel invoices.",
    response_model=List[InvoiceResponse],
)
def get_client_invoices(client_id: str):
    client = database.get_client_by_id(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' tidak ditemukan",
        )
    return database.get_invoices_by_client_id(client_id)


@app.get(
    "/invoices",
    summary="Daftar invoices",
    description="Mengambil daftar invoice dari tabel invoices, dengan filter opsional client_id.",
    response_model=List[InvoiceResponse],
)
def get_invoices(client_id: Optional[str] = Query(None, description="Filter invoice berdasarkan client_id")):
    if client_id:
        return database.get_invoices_by_client_id(client_id)
    return database.get_all_invoices()


@app.get(
    "/knowledge-bases",
    summary="Menampilkan knowledge base",
    description="Mengambil seluruh data knowledge base mentah dari database.",
    response_model=List[KnowledgeBaseResponse],
)
def get_knowledge_bases(category: Optional[str] = Query(None, description="Filter berdasarkan kategori")):
    category_val = category if isinstance(category, str) else None
    return database.get_all_knowledge_bases(category=category_val)


@app.post(
    "/knowledge-bases",
    summary="Menambahkan knowledge base",
    description="Menambahkan entri knowledge base baru ke dalam database SQLite.",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_base(req: KnowledgeBaseCreateRequest):
    import json
    import gemini_tools
    text_to_embed = f"Keyword: {req.keyword_triggers}\nJudul: {req.title}\nKonten: {req.content}"
    vector = gemini_tools.get_text_embedding(text_to_embed)
    embedding_json = json.dumps(vector) if vector else None

    result = database.add_knowledge_base(
        category=req.category,
        keyword_triggers=req.keyword_triggers,
        title=req.title,
        content=req.content,
        embedding=embedding_json,
    )
    return result


@app.get(
    "/conversations/{conversation_id}",
    summary="Mengambil riwayat percakapan",
    description="Mengambil data sesi percakapan beserta seluruh pesan chat terkait sesuai batas limit yang ditentukan.",
    response_model=ConversationResponse,
    responses={
        200: {
            "description": "Data dan riwayat pesan percakapan berhasil ditemukan",
        },
        404: {
            "description": "Percakapan tidak ditemukan",
        },
        403: {
            "description": "Akses ditolak karena sesi bukan milik klien yang bersangkutan",
        },
    },
)
def get_conversation(
    conversation_id: str,
    client_id: Optional[str] = Query(None, description="Client ID untuk validasi kepemilikan sesi percakapan"),
    limit: int = Query(20, description="Batas jumlah riwayat pesan yang diambil"),
):
    valid_client_id = client_id if isinstance(client_id, str) and client_id.strip() else None
    actual_limit = limit if isinstance(limit, int) else 20
    if valid_client_id:
        client = database.get_client_by_id(valid_client_id.strip())
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{valid_client_id.strip()}' tidak ditemukan",
            )
    conv = database.get_conversation_by_id(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' tidak ditemukan",
        )
    if valid_client_id:
        if conv.get("client_id") != valid_client_id.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak: Percakapan '{conversation_id}' bukan milik klien '{valid_client_id.strip()}'.",
            )
    messages = database.get_conversation_messages(conversation_id, limit=actual_limit)
    return {
        "conversation_id": conv["conversation_id"],
        "client_id": conv["client_id"],
        "created_at": conv["created_at"],
        "updated_at": conv["updated_at"],
        "total_messages": len(messages),
        "messages": messages,
    }


@app.post(
    "/chat",
    summary="Memproses pesan chatbot dan menghasilkan balasan",
    description="Endpoint utama chatbot AI untuk melayani pertanyaan klien, eksekusi tool calling, dan policy check.",
    response_model=ChatResponse,
)
def chat_endpoint(req: ChatRequest):
    try:
        return chatbot_engine.process_chat_message(
            client_id=req.client_id,
            message=req.message,
            conversation_id=req.conversation_id,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Terjadi kesalahan: {str(e)}")


@app.delete(
    "/conversations/{conversation_id}",
    summary="Menghapus sesi percakapan",
    description="Menghapus data sesi percakapan beserta seluruh histori pesan terkait.",
    responses={
        200: {"description": "Sesi percakapan berhasil dihapus"},
        404: {"description": "Percakapan atau klien tidak ditemukan"},
        403: {"description": "Akses percakapan ditolak"},
    },
)
def delete_conversation_endpoint(
    conversation_id: str,
    client_id: Optional[str] = Query(None, description="Client ID untuk validasi kepemilikan sesi percakapan"),
):
    valid_client_id = client_id if isinstance(client_id, str) and client_id.strip() else None
    if valid_client_id:
        client = database.get_client_by_id(valid_client_id.strip())
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{valid_client_id.strip()}' tidak ditemukan",
            )
    conv = database.get_conversation_by_id(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' tidak ditemukan",
        )
    if valid_client_id:
        if conv.get("client_id") != valid_client_id.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak: Percakapan '{conversation_id}' bukan milik klien '{valid_client_id.strip()}'.",
            )
    database.delete_conversation_by_id(conversation_id)
    return {
        "success": True,
        "message": f"Percakapan '{conversation_id}' berhasil dihapus",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
