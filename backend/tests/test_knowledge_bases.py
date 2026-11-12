import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database
from main import KnowledgeBaseCreateRequest, create_knowledge_base, get_knowledge_bases


def test_get_all_knowledge_bases_from_db():
    kb_list = database.get_all_knowledge_bases()
    assert len(kb_list) >= 4
    for kb in kb_list:
        assert "id" in kb
        assert "category" in kb
        assert "keyword_triggers" in kb
        assert "title" in kb
        assert "content" in kb


def test_get_knowledge_bases_endpoint():
    kb_list = get_knowledge_bases()
    assert len(kb_list) >= 4
    categories = [kb["category"] for kb in kb_list]
    assert "rekening" in categories
    assert "layanan" in categories
    assert "kebijakan" in categories
    assert "operasional" in categories


def test_get_knowledge_bases_filter_category():
    kb_rekening = get_knowledge_bases(category="rekening")
    assert len(kb_rekening) == 1
    assert kb_rekening[0]["category"] == "rekening"
    assert "BCA" in kb_rekening[0]["content"]


def test_create_knowledge_base_endpoint():
    req = KnowledgeBaseCreateRequest(
        category="promo",
        keyword_triggers="promo, diskon, potongan harga",
        title="Promo Akhir Tahun",
        content="Diskon 20% untuk semua paket website dan SEO hingga akhir tahun."
    )
    res = create_knowledge_base(req)
    assert res["id"] is not None
    assert res["category"] == "promo"
    assert res["title"] == "Promo Akhir Tahun"
    assert res["keyword_triggers"] == "promo, diskon, potongan harga"

    # Verifikasi tersimpan di database
    created_id = res["id"]
    try:
        kb_all = database.get_all_knowledge_bases(category="promo")
        assert any(item["id"] == created_id for item in kb_all)
    finally:
        # Cleanup
        conn = database.get_db_connection()
        try:
            conn.execute("DELETE FROM knowledge_bases WHERE id = ?", (created_id,))
            conn.commit()
        finally:
            conn.close()

