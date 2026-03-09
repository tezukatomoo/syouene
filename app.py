"""共同住宅 省エネ計算 Web アプリケーション"""

import json
import traceback

import numpy as np
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


# ---------- デフォルト仕様 ----------

DEFAULTS_APARTMENT = {
    "region": 6,
    "type": "一般住宅",
    "tatekata": "共同住宅",
    "sol_region": None,
    "evaluation_method": "住戸全体を対象に評価する",
    "A_A": 70.00,
    "A_MR": 24.22,
    "A_OR": 29.75,
    "NV_MR": 0,
    "NV_OR": 0,
    "TS": False,
    "r_A_ufvnt": None,
    "underfloor_insulation": None,
    "mode_H": "居室のみを暖房する方式でかつ主たる居室とその他の居室ともに温水暖房を設置する場合に該当しない場合",
    "mode_C": "居室のみを冷房する方式",
    "H_A": None,
    "H_MR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "H_OR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "H_HS": None,
    "C_A": None,
    "C_MR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "C_OR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "HW": {
        "has_bath": True,
        "hw_type": "ガス従来型給湯機",
        "hybrid_category": None,
        "e_rtd": None,
        "e_dash_rtd": None,
        "kitchen_watersaving_A": False,
        "kitchen_watersaving_C": False,
        "shower_watersaving_A": False,
        "shower_watersaving_B": False,
        "washbowl_watersaving_C": False,
        "bath_insulation": False,
        "bath_function": "ふろ給湯機(追焚あり)",
        "pipe_diameter": "上記以外",
    },
    "V": {
        "type": "ダクト式第二種換気設備又はダクト式第三種換気設備",
        "input": "評価しない",
        "N": 0.5,
    },
    "HEX": None,
    "L": {
        "has_OR": True,
        "has_NO": True,
        "A_OR": 29.75,
        "MR_installed": "設置しない",
        "OR_installed": "設置しない",
        "NO_installed": "設置しない",
    },
    "SHC": None,
    "PV": None,
    "CG": None,
    "ENV": {
        "method": "当該住宅の外皮面積の合計を用いて評価する",
        "A_env": 238.22,
        "A_A": 70.00,
        "U_A": 0.87,
        "eta_A_H": 4.3,
        "eta_A_C": 2.8,
    },
}

DEFAULTS_DETACHED = {
    "region": 6,
    "type": "一般住宅",
    "tatekata": "戸建住宅",
    "sol_region": None,
    "evaluation_method": "住戸全体を対象に評価する",
    "A_A": 120.08,
    "A_MR": 29.81,
    "A_OR": 51.34,
    "NV_MR": 0,
    "NV_OR": 0,
    "TS": False,
    "r_A_ufvnt": None,
    "underfloor_insulation": None,
    "mode_H": "居室のみを暖房する方式でかつ主たる居室とその他の居室ともに温水暖房を設置する場合に該当しない場合",
    "mode_C": "居室のみを冷房する方式",
    "H_A": None,
    "H_MR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "H_OR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "H_HS": None,
    "C_A": None,
    "C_MR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "C_OR": {
        "type": "ルームエアコンディショナー",
        "e_class": None,
        "dualcompressor": False,
    },
    "HW": {
        "has_bath": True,
        "hw_type": "ガス従来型給湯機",
        "hybrid_category": None,
        "e_rtd": None,
        "e_dash_rtd": None,
        "kitchen_watersaving_A": False,
        "kitchen_watersaving_C": False,
        "shower_watersaving_A": False,
        "shower_watersaving_B": False,
        "washbowl_watersaving_C": False,
        "bath_insulation": False,
        "bath_function": "ふろ給湯機(追焚あり)",
        "pipe_diameter": "上記以外",
    },
    "V": {
        "type": "ダクト式第二種換気設備又はダクト式第三種換気設備",
        "input": "評価しない",
        "N": 0.5,
    },
    "HEX": None,
    "L": {
        "has_OR": True,
        "has_NO": True,
        "A_OR": 51.34,
        "MR_installed": "設置しない",
        "OR_installed": "設置しない",
        "NO_installed": "設置しない",
    },
    "SHC": None,
    "PV": None,
    "CG": None,
    "ENV": {
        "method": "当該住宅の外皮面積の合計を用いて評価する",
        "A_env": 307.51,
        "A_A": 120.08,
        "U_A": 0.87,
        "eta_A_H": 4.3,
        "eta_A_C": 2.8,
    },
}


# ---------- 外皮基準値 ----------

# 省エネ基準 UA値 (W/m2K)  地域区分 1-8
STANDARD_UA = {
    1: 0.46, 2: 0.46, 3: 0.56, 4: 0.75,
    5: 0.87, 6: 0.87, 7: 0.87, 8: None,  # 8地域はUA基準なし
}

# 省エネ基準 ηAC値  地域区分 1-8
# 共同住宅の値
STANDARD_ETA_AC_APARTMENT = {
    1: None, 2: None, 3: None, 4: None,
    5: 3.0, 6: 2.8, 7: 2.7, 8: 6.7,
}
# 戸建住宅の値
STANDARD_ETA_AC_DETACHED = {
    1: None, 2: None, 3: None, 4: None,
    5: 3.0, 6: 2.8, 7: 2.7, 8: 3.2,
}

# 方位係数 (暖房期 νH, 冷房期 νC) — 6地域の代表値
# 方位: N, NE, E, SE, S, SW, W, NW, 上(屋根), 下(床)
NU_H = {
    "北": 0.263, "北東": 0.263, "東": 0.407, "南東": 0.516,
    "南": 0.504, "南西": 0.516, "西": 0.407, "北西": 0.263,
    "上": 0.906, "下": 0.000,
}
NU_C = {
    "北": 0.329, "北東": 0.390, "東": 0.488, "南東": 0.454,
    "南": 0.345, "南西": 0.454, "西": 0.488, "北西": 0.390,
    "上": 0.901, "下": 0.000,
}


def _safe_float(v):
    """numpy/NaN を JSON-safe な値に変換"""
    if v is None:
        return None
    if isinstance(v, (np.floating, np.integer)):
        v = float(v)
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return None
    return v


def _build_spec(data: dict) -> dict:
    """フロントエンドから送られた JSON を pyhees の spec 辞書に変換"""
    region = int(data.get("region", 6))
    tatekata = data.get("tatekata", "共同住宅")
    sol_region = data.get("sol_region")
    if sol_region is not None and sol_region != "":
        sol_region = int(sol_region)
    else:
        sol_region = None

    A_A = float(data.get("A_A", 70.0))
    A_MR = float(data.get("A_MR", 24.22))
    A_OR = float(data.get("A_OR", 29.75))

    # --- 暖房 ---
    mode_H = data.get("mode_H", "居室のみを暖房する方式でかつ主たる居室とその他の居室ともに温水暖房を設置する場合に該当しない場合")
    h_mr_type = data.get("H_MR_type", "ルームエアコンディショナー")
    h_or_type = data.get("H_OR_type", "ルームエアコンディショナー")

    H_A = None
    H_MR = None
    H_OR = None
    H_HS = None

    if mode_H == "住戸全体を連続的に暖房する方式":
        ha_type = data.get("H_A_type", "ルームエアコンディショナー")
        H_A = {"type": ha_type, "e_class": None, "dualcompressor": False}
    elif mode_H == "設置しない":
        pass
    else:
        H_MR = {"type": h_mr_type, "e_class": None, "dualcompressor": False}
        H_OR = {"type": h_or_type, "e_class": None, "dualcompressor": False}

    # 温水暖房の場合
    if h_mr_type in ("温水暖房用パネルラジエーター", "温水暖房用床暖房") or \
       h_or_type in ("温水暖房用パネルラジエーター", "温水暖房用床暖房"):
        hs_type = data.get("H_HS_type", "ガス従来型温水暖房機")
        H_HS = {
            "type": hs_type,
            "e_rtd_hs": float(data.get("H_HS_e_rtd_hs", 0.82)),
            "pipe_insulation": data.get("H_HS_pipe_insulation", True),
            "underfloor_pipe_insulation": data.get("H_HS_underfloor_pipe_insulation", False),
        }

    # --- 冷房 ---
    mode_C = data.get("mode_C", "居室のみを冷房する方式")
    c_mr_type = data.get("C_MR_type", "ルームエアコンディショナー")
    c_or_type = data.get("C_OR_type", "ルームエアコンディショナー")

    C_A = None
    C_MR = None
    C_OR = None

    if mode_C == "住戸全体を連続的に冷房する方式":
        ca_type = data.get("C_A_type", "ルームエアコンディショナー")
        C_A = {"type": ca_type, "e_class": None, "dualcompressor": False}
    elif mode_C == "設置しない":
        pass
    else:
        C_MR = {"type": c_mr_type, "e_class": None, "dualcompressor": False}
        C_OR = {"type": c_or_type, "e_class": None, "dualcompressor": False}

    # --- 給湯 ---
    hw_type = data.get("hw_type", "ガス従来型給湯機")
    has_bath = data.get("has_bath", True)
    if isinstance(has_bath, str):
        has_bath = has_bath.lower() in ("true", "1", "yes")
    HW = {
        "has_bath": has_bath,
        "hw_type": hw_type,
        "hybrid_category": None,
        "e_rtd": None,
        "e_dash_rtd": None,
        "kitchen_watersaving_A": data.get("kitchen_watersaving_A", False),
        "kitchen_watersaving_C": data.get("kitchen_watersaving_C", False),
        "shower_watersaving_A": data.get("shower_watersaving_A", False),
        "shower_watersaving_B": data.get("shower_watersaving_B", False),
        "washbowl_watersaving_C": data.get("washbowl_watersaving_C", False),
        "bath_insulation": data.get("bath_insulation", False),
        "bath_function": data.get("bath_function", "ふろ給湯機(追焚あり)"),
        "pipe_diameter": data.get("pipe_diameter", "上記以外"),
    }
    # bool変換
    for key in ("kitchen_watersaving_A", "kitchen_watersaving_C",
                "shower_watersaving_A", "shower_watersaving_B",
                "washbowl_watersaving_C", "bath_insulation"):
        v = HW[key]
        if isinstance(v, str):
            HW[key] = v.lower() in ("true", "1", "yes")

    # --- 換気 ---
    v_type = data.get("V_type", "ダクト式第二種換気設備又はダクト式第三種換気設備")
    V = {
        "type": v_type,
        "input": "評価しない",
        "N": float(data.get("V_N", 0.5)),
    }
    HEX = None

    # --- 照明 ---
    L = {
        "has_OR": True,
        "has_NO": True,
        "A_OR": A_OR,
        "MR_installed": data.get("L_MR_installed", "設置しない"),
        "OR_installed": data.get("L_OR_installed", "設置しない"),
        "NO_installed": data.get("L_NO_installed", "設置しない"),
    }

    # --- 外皮 ---
    ENV = {
        "method": data.get("ENV_method", "当該住宅の外皮面積の合計を用いて評価する"),
        "A_env": float(data.get("A_env", 238.22 if tatekata == "共同住宅" else 307.51)),
        "A_A": A_A,
        "U_A": float(data.get("U_A", 0.87)),
        "eta_A_H": float(data.get("eta_A_H", 4.3)),
        "eta_A_C": float(data.get("eta_A_C", 2.8)),
    }

    # --- 再エネ ---
    SHC = None
    PV = None
    CG = None

    if data.get("PV_enabled"):
        pv_enabled = data["PV_enabled"]
        if isinstance(pv_enabled, str):
            pv_enabled = pv_enabled.lower() in ("true", "1", "yes")
        if pv_enabled:
            PV = {
                "type": data.get("PV_type", "結晶シリコン系"),
                "P_alpha": float(data.get("PV_P_alpha", 0)),
                "P_beta": float(data.get("PV_P_beta", 30)),
                "P_p_i": float(data.get("PV_P_p_i", 4.0)),
            }

    spec = {
        "region": region,
        "type": "一般住宅",
        "tatekata": tatekata,
        "sol_region": sol_region,
        "evaluation_method": "住戸全体を対象に評価する",
        "A_A": A_A,
        "A_MR": A_MR,
        "A_OR": A_OR,
        "NV_MR": int(data.get("NV_MR", 0)),
        "NV_OR": int(data.get("NV_OR", 0)),
        "TS": False,
        "r_A_ufvnt": None,
        "underfloor_insulation": None,
        "mode_H": mode_H,
        "mode_C": mode_C,
        "H_A": H_A,
        "H_MR": H_MR,
        "H_OR": H_OR,
        "H_HS": H_HS,
        "C_A": C_A,
        "C_MR": C_MR,
        "C_OR": C_OR,
        "HW": HW,
        "V": V,
        "HEX": HEX,
        "L": L,
        "SHC": SHC,
        "PV": PV,
        "CG": CG,
        "ENV": ENV,
    }
    return spec


# ---------- ルート ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/defaults", methods=["POST"])
def api_defaults():
    data = request.get_json(silent=True) or {}
    tatekata = data.get("tatekata", "共同住宅")
    if tatekata == "共同住宅":
        return jsonify(DEFAULTS_APARTMENT)
    else:
        return jsonify(DEFAULTS_DETACHED)


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "リクエストボディが空です"}), 400

        spec = _build_spec(data)

        # pyhees で計算
        from pyhees.section2_2 import calc_E_T

        results = calc_E_T(spec)

        # 結果を整形
        # results は tuple: (E_T_dict, E_dash_T_dict, E_pri_dict, E_sec_dict)
        # 実際の返却形式は pyhees のバージョンにより多少異なる可能性あり
        if isinstance(results, tuple):
            if len(results) >= 4:
                e_total = results[0]
                e_dash = results[1]
                e_detail = results[2]
                e_secondary = results[3]
            else:
                return jsonify({"error": f"計算結果の形式が想定外です (length={len(results)})"}), 500
        else:
            return jsonify({"error": "計算結果の形式が想定外です"}), 500

        # 基準値計算
        from pyhees.section2_3 import calc_E_ST
        from pyhees.section2_4 import calc_BEI

        standard_results = calc_E_ST(spec)
        e_st_total = {}
        e_dash_st = {}
        e_st_detail = {}
        if isinstance(standard_results, tuple) and len(standard_results) >= 3:
            e_st_total = standard_results[0] if isinstance(standard_results[0], dict) else {}
            e_dash_st = standard_results[1] if isinstance(standard_results[1], dict) else {}
            e_st_detail = standard_results[2] if isinstance(standard_results[2], dict) else {}

        standard_gj = _safe_float(e_st_total.get("E_ST_gn_du_p"))

        # BEI 計算: pyhees 公式関数を使用
        # BEI = E_dash_T (その他除く設計値) / E_dash_ST (その他除く基準値)
        # 小数点以下2桁目を切り上げ
        bei_dict = calc_BEI(e_dash, e_dash_st)
        bei = _safe_float(bei_dict.get("BEI_gn_du"))

        # 外皮基準適合判定
        region = spec["region"]
        tatekata = spec["tatekata"]
        u_a = spec["ENV"]["U_A"]
        eta_a_c = spec["ENV"]["eta_A_C"]

        std_ua = STANDARD_UA.get(region)
        if tatekata == "共同住宅":
            std_eta_ac = STANDARD_ETA_AC_APARTMENT.get(region)
        else:
            std_eta_ac = STANDARD_ETA_AC_DETACHED.get(region)

        env_compliance = {
            "U_A": u_a,
            "U_A_standard": std_ua,
            "U_A_pass": std_ua is None or u_a <= std_ua,
            "eta_A_C": eta_a_c,
            "eta_A_C_standard": std_eta_ac,
            "eta_A_C_pass": std_eta_ac is None or eta_a_c <= std_eta_ac,
        }

        response = {
            "success": True,
            "design": {
                "E_T": _safe_float(e_total.get("E_T_gn_du")),
                "E_T_indc": _safe_float(e_total.get("E_T_indc_du")),
                "E_T_lcb": _safe_float(e_total.get("E_T_lcb_du")),
                "E_dash_T": _safe_float(e_dash.get("E_dash_T_gn_du")),
            },
            "detail": {
                "E_H": _safe_float(e_detail.get("E_H", 0)),
                "E_C": _safe_float(e_detail.get("E_C", 0)),
                "E_V": _safe_float(e_detail.get("E_V", 0)),
                "E_L": _safe_float(e_detail.get("E_L", 0)),
                "E_W": _safe_float(e_detail.get("E_W", 0)),
                "E_S": _safe_float(e_detail.get("E_S", 0)),
                "E_M": _safe_float(e_detail.get("E_M", 0)),
            },
            "secondary": {
                "E_E": _safe_float(e_secondary.get("E_E", 0)),
                "E_G": _safe_float(e_secondary.get("E_G", 0)),
                "E_K": _safe_float(e_secondary.get("E_K", 0)),
            },
            "standard": {
                "E_ST": standard_gj,
                "E_dash_ST": _safe_float(e_dash_st.get("E_dash_ST_gn_du")),
                "detail": {
                    "E_SH": _safe_float(e_st_detail.get("E_SH", 0)),
                    "E_SC": _safe_float(e_st_detail.get("E_SC", 0)),
                    "E_SV": _safe_float(e_st_detail.get("E_SV", 0)),
                    "E_SL": _safe_float(e_st_detail.get("E_SL", 0)),
                    "E_SW": _safe_float(e_st_detail.get("E_SW", 0)),
                    "E_SM": _safe_float(e_st_detail.get("E_SM", 0)),
                },
            },
            "BEI": bei,
            "BEI_all": {
                "BEI_gn": _safe_float(bei_dict.get("BEI_gn_du")),
                "BEI_indc": _safe_float(bei_dict.get("BEI_indc_du")),
                "BEI_lcb": _safe_float(bei_dict.get("BEI_lcb_du")),
            },
            "env_compliance": env_compliance,
        }
        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/calc_envelope", methods=["POST"])
def api_calc_envelope():
    """外皮部位データからUA値・ηAH・ηACを算出"""
    try:
        data = request.get_json()
        parts = data.get("parts", [])
        region = int(data.get("region", 6))
        tatekata = data.get("tatekata", "共同住宅")

        if not parts:
            return jsonify({"error": "部位データがありません"}), 400

        # UA = Σ(Ui × Ai) + Σ(ψj × Lj) / A_env
        total_q = 0.0       # Σ(Ui × Ai) — 熱損失量
        total_area = 0.0     # A_env — 外皮面積合計
        total_mh = 0.0       # Σ(νH × ηi × Ai) — 暖房期日射熱取得量
        total_mc = 0.0       # Σ(νC × ηi × Ai) — 冷房期日射熱取得量
        total_psi_l = 0.0    # Σ(ψj × Lj) — 熱橋の線熱貫流率

        for p in parts:
            part_type = p.get("type", "")
            area = float(p.get("area", 0))
            u_value = float(p.get("u_value", 0))
            h_value = float(p.get("h_value", 1.0))  # 温度差係数
            direction = p.get("direction", "南")
            eta_value = float(p.get("eta_value", 0))  # 日射熱取得率
            psi = float(p.get("psi", 0))  # 線熱貫流率
            length = float(p.get("length", 0))  # 熱橋長さ

            if part_type == "線熱橋":
                # 線熱橋: 面積をA_envに加算しない、ψ×L×H×按分数のみ
                anbun = float(p.get("anbun", 1.0))
                total_psi_l += psi * length * h_value * anbun
            else:
                total_area += area
                total_q += u_value * area * h_value  # q = U × A × H

                nu_h = NU_H.get(direction, 0.504)
                nu_c = NU_C.get(direction, 0.345)
                total_mh += nu_h * eta_value * area
                total_mc += nu_c * eta_value * area

        if total_area <= 0:
            return jsonify({"error": "外皮面積が0です"}), 400

        u_a = round((total_q + total_psi_l) / total_area, 2)
        eta_a_h = round(total_mh / total_area * 100, 1)
        eta_a_c = round(total_mc / total_area * 100, 1)

        # 基準適合判定
        std_ua = STANDARD_UA.get(region)
        if tatekata == "共同住宅":
            std_eta_ac = STANDARD_ETA_AC_APARTMENT.get(region)
        else:
            std_eta_ac = STANDARD_ETA_AC_DETACHED.get(region)

        result = {
            "U_A": u_a,
            "eta_A_H": eta_a_h,
            "eta_A_C": eta_a_c,
            "A_env": round(total_area, 2),
            "q_total": round(total_q + total_psi_l, 2),
            "standard": {
                "U_A": std_ua,
                "eta_A_C": std_eta_ac,
            },
            "compliance": {
                "U_A_pass": std_ua is None or u_a <= std_ua,
                "eta_A_C_pass": std_eta_ac is None or eta_a_c <= std_eta_ac,
            },
        }
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
