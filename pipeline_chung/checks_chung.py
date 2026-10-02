"""Kiểm tra chung bằng Python cho mọi dạng bài (bước 1.3 và 2.5 của workflow tổng quát).

Mỗi hàm trả về dict {"loi": [...], "canh_bao": [...], "so_lieu": {...}}.
Kiểm tra riêng của từng dạng bài viết trong thư mục dạng bài và gộp kết quả vào đây.
"""
import collections
import json
import re

from .common import (FURI_RE, JA_RE, LOCK_RE, VI_DIACRITIC_RE, HANGUL_RE, drop_lang, iter_lang_fields,
                     iter_strings, norm_ja, path_str, strip_marks, vi_words)

try:
    import jsonschema
    _V = getattr(jsonschema, "Draft202012Validator", None) or jsonschema.Draft7Validator
except ImportError:  # pragma: no cover
    jsonschema, _V = None, None

# từ khung không tính khi đo độ phủ (template JSON đã tách ra)
STRUCT_WORDS = {"nghĩa", "là", "có", "ví", "dụ", "mang"}


def result():
    return {"loi": [], "canh_bao": [], "so_lieu": {}}


def schema_errors(doc, schema):
    if _V is None:
        return ["Chưa cài thư viện jsonschema – không kiểm tra được schema"]
    return [f"Schema: {path_str(tuple(e.path))} – {e.message[:180]}"
            for e in sorted(_V(schema).iter_errors(doc), key=lambda e: list(e.path))]


def _all_text(doc):
    return "\n".join(s for _, s in iter_strings(doc))


def _pairs_counter(text):
    return collections.Counter(FURI_RE.findall(text or ""))


def furigana_problems(src_text, doc_text):
    """So danh sách cặp (chữ gốc, cách đọc) giữa bản gốc đã chuẩn hóa và JSON."""
    out = []
    a, b = _pairs_counter(src_text), _pairs_counter(doc_text)
    if a != b:
        miss, extra = a - b, b - a
        if miss:
            out.append(f"Furigana bị mất/sai: {[f'{k}《{v}》' for k, v in list(miss.elements())[:6]]}")
        if extra:
            out.append(f"Furigana thừa/sai: {[f'{k}《{v}》' for k, v in list(extra.elements())[:6]]}")
    n_pairs = sum(b.values())
    if doc_text.count("《") != n_pairs or doc_text.count("》") != n_pairs or doc_text.count("｜") != n_pairs:
        out.append("Ký hiệu furigana sai cách ghi (《》 thiếu ｜, hoặc ｜ không đi kèm 《》)")
    return out


def check_vi(doc, schema, src_text, src_vi_text, expected, cfg_checks, strip_labels=lambda t: t,
             marks_src=None, furi_src_text=None, furi_skip=()):
    """Kiểm tra chung giai đoạn 1.

    doc           JSON tiếng Việt cần kiểm tra
    src_text      toàn bộ lời giải gốc đã chuẩn hóa (để so tiếng Nhật, furigana)
    src_vi_text   phần chữ tiếng Việt của lời giải gốc (để đo độ phủ); strip_labels bỏ nhãn cố định
    expected      {"question_id", "cau_con", "dap_an_so"}
    marks_src     (WF chung mục 3a) danh sách đoạn { } của bản gốc; có thì so với các đoạn { } trong JSON,
                  không có thì dùng quy tắc cũ "mỗi chuỗi tối đa 1 cặp"
    furi_src_text bản gốc dùng để so furigana (bỏ phần trùng lặp đã khai báo); mặc định = src_text
    furi_skip     các đường dẫn (tuple) trong JSON không tính khi so furigana (bản sao của trường khác)
    """
    r = result()
    r["loi"] += schema_errors(doc, schema)

    # định danh
    for k in ("question_id", "cau_con"):
        if str(doc.get(k)) != str(expected[k]):
            r["loi"].append(f"{k} = {doc.get(k)} ≠ {expected[k]}")

    # tiếng Nhật không bị mất
    dump = norm_ja(_all_text(doc))
    runs = sorted({m for m in JA_RE.findall(strip_marks(src_text))})
    missing = [x for x in runs if norm_ja(x) not in dump]
    if missing:
        r["loi"].append(f"Mất {len(missing)} đoạn tiếng Nhật: {missing[:8]}")

    # tiếng Việt: độ phủ và từ thừa
    src = collections.Counter(w for w in vi_words(strip_labels(src_vi_text)) if w not in STRUCT_WORDS)
    out = collections.Counter(w for _, o in iter_lang_fields(doc) for w in vi_words(o["vi"]) if w not in STRUCT_WORDS)
    cov = extra = None
    if src:
        cov = sum((src & out).values()) / sum(src.values())
        extra = sum((out - src).values()) / max(1, sum(out.values()))
        if cov < cfg_checks.get("vi_word_coverage_min", 0.97):
            r["loi"].append(f"Độ phủ tiếng Việt {cov:.1%} (thiếu: {[w for w, _ in (src - out).most_common(12)]})")
        if extra > cfg_checks.get("vi_extra_words_max", 0.05):
            r["canh_bao"].append(f"Từ thừa {extra:.1%} (vd: {[w for w, _ in (out - src).most_common(12)]})")
    r["so_lieu"].update({"do_phu_vi": cov, "tu_thua_vi": extra,
                         "tu_moi": [w for w, _ in (out - src).most_common(20)] if src else []})

    for fp, o in iter_lang_fields(doc):
        t = o["vi"]
        if not t.strip():
            r["loi"].append(f"{path_str(fp)}: trường vi để trống (không có nội dung thì dùng null)")
        if t.count("⟪") != t.count("⟫"):
            r["loi"].append(f"{path_str(fp)}: số ⟪ và ⟫ không bằng nhau")
        for inner in LOCK_RE.findall(t):
            if not JA_RE.search(strip_marks(inner)):
                r["canh_bao"].append(f"{path_str(fp)}: ⟪{inner}⟫ không chứa tiếng Nhật")
        outside = JA_RE.findall(strip_marks(LOCK_RE.sub("", t)))
        if outside:
            r["canh_bao"].append(f"{path_str(fp)}: còn tiếng Nhật chưa bọc ⟪ ⟫: {outside[:5]}")

    # đánh dấu { }
    for sp, s in iter_strings(doc):
        if not re.fullmatch(r"[^{}]*(\{[^{}]*\}[^{}]*)*", s):
            r["loi"].append(f"{path_str(sp)}: dấu {{ }} không cân bằng hoặc lồng nhau")
        elif marks_src is None and s.count("{") > 1:
            r["loi"].append(f"{path_str(sp)}: dấu {{ }} sai (mỗi câu tối đa 1 cặp)")
    if marks_src is not None:
        from .normalize import mark_segments
        a = collections.Counter(x for x in marks_src if x)
        b = collections.Counter(x for _, s in iter_strings(doc) for x in mark_segments(s) if x)
        if a != b:
            if a - b:
                r["loi"].append(f"Đánh dấu {{ }} bị mất/sai so với bản gốc: {list((a - b).elements())[:6]}")
            if b - a:
                r["loi"].append(f"Đánh dấu {{ }} thừa so với bản gốc: {list((b - a).elements())[:6]}")

    skip = {tuple(p_) for p_ in furi_skip}
    doc_furi = "\n".join(s for sp, s in iter_strings(doc) if tuple(sp) not in skip)
    r["loi"] += furigana_problems(src_text if furi_src_text is None else furi_src_text, doc_furi)
    return r


def check_ko(doc_ko, vi_final, schema, lang, cfg_checks, is_style_field=lambda path: False):
    """Kiểm tra chung giai đoạn 2: doc_ko = JSON đã có bản dịch; vi_final = JSON tiếng Việt đã chốt."""
    r = result()
    base = drop_lang(doc_ko, lang)
    r["loi"] += schema_errors(base, schema)
    if base != vi_final:
        a = dict(iter_strings(base)); b = dict(iter_strings(vi_final))
        diff = [path_str(k) for k in set(a) | set(b) if a.get(k) != b.get(k)]
        r["loi"].append(f"Phần không phải '{lang}' khác JSON tiếng Việt đã chốt: {sorted(diff)[:6] or '(cấu trúc khác)'}")

    lo, hi = cfg_checks.get("ko_vi_length_ratio", [0.3, 1.5])
    for fp, o in iter_lang_fields(doc_ko):
        ps, vi, ko = path_str(fp), o["vi"], o.get(lang)
        if not isinstance(ko, str) or not ko.strip():
            r["loi"].append(f"{ps}: thiếu bản dịch '{lang}'")
            continue
        bare = LOCK_RE.sub("", ko)
        if VI_DIACRITIC_RE.search(bare):
            r["loi"].append(f"{ps}: còn chữ tiếng Việt trong bản dịch")
        if sorted(LOCK_RE.findall(vi)) != sorted(LOCK_RE.findall(ko)):
            r["loi"].append(f"{ps}: nội dung ⟪ ⟫ khác bản tiếng Việt")
        ja_out_vi = set(JA_RE.findall(strip_marks(LOCK_RE.sub("", vi))))
        ja_out_ko = [x for x in JA_RE.findall(strip_marks(bare)) if x not in ja_out_vi]
        if ja_out_ko:
            r["loi"].append(f"{ps}: có tiếng Nhật nằm ngoài ⟪ ⟫: {ja_out_ko[:5]}")
        if (vi.count("{"), vi.count("}")) != (ko.count("{"), ko.count("}")):
            r["loi"].append(f"{ps}: số dấu {{ }} khác bản tiếng Việt")
        if _pairs_counter(vi) != _pairs_counter(ko):
            r["loi"].append(f"{ps}: furigana khác bản tiếng Việt")
        if lang == "ko" and not HANGUL_RE.search(bare) and strip_marks(bare).strip():
            r["canh_bao"].append(f"{ps}: bản dịch không có chữ Hàn")
        ratio = len(strip_marks(ko)) / max(1, len(strip_marks(vi)))
        if len(strip_marks(vi)) >= 30 and not (lo <= ratio <= hi):     # chuỗi ngắn (nghĩa từ…) không đo tỷ lệ
            r["canh_bao"].append(f"{ps}: tỷ lệ độ dài KO/VI = {ratio:.2f}")
        if lang == "ko" and is_style_field(fp):
            line = bare.strip().split("\n")[-1].strip()
            # dòng cuối là mục danh sách, ví dụ kèm chú thích trong ngoặc… thì không xét văn phong
            if re.match(r"^(\d+\s*[\.\)]|-|\*)", line) or re.search(r"\)\s*\.?$", line):
                continue
            last = re.sub(r"[\s\.\)\"」』⟫}]+$", "", line)
            if last and not re.search(r"(니다|니까|세요|십시오|습니다)$", last) and HANGUL_RE.search(last[-1:] or ""):
                r["canh_bao"].append(f"{ps}: câu cuối không dùng văn phong -습니다")
    return r
