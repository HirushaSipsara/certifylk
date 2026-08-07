"""Seed SLS Mark certification data for Fresh Fruit Cordial (pilot).

All requirement rows have content_verified=False — a UI banner informs users.
Content is based on publicly available SLSI guidance, the Sri Lanka Food Act
(No. 26 of 1980), and standard GMP principles for cordial manufacturing.
It has NOT been verified against the purchased SLSI standard text.

Revision ID: 20260807_0003
Revises: 20260807_0002
"""

from datetime import date

import sqlalchemy as sa

from alembic import op

revision = "20260807_0003"
down_revision = "20260807_0002"
branch_labels = None
depends_on = None

REVIEWED = date(2026, 8, 7)
EFFECTIVE = date(2026, 8, 7)

# Stable UUIDs for seed rows
CAT_FOOD_PRODUCTS = "11111111-1111-1111-1111-111111111111"
PROD_CORDIAL = "22222222-2222-2222-2222-222222222222"


def upgrade() -> None:
    conn = op.get_bind()

    # ── Certification bodies ──────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            INSERT INTO certification_bodies (id, name, short_code, website_url, description)
            VALUES
              ('SLSI', 'Sri Lanka Standards Institution', 'SLSI',
               'https://www.slsi.lk',
               'Government body responsible for standardisation and product certification in Sri Lanka.'),
              ('CAA', 'Consumer Affairs Authority', 'CAA',
               'https://www.caa.gov.lk',
               'Statutory body regulating food labelling and consumer protection in Sri Lanka.'),
              ('ISO', 'International Organization for Standardization', 'ISO',
               'https://www.iso.org',
               'International standards body — ISO 22000 Food Safety Management Systems.')
            ON CONFLICT (id) DO NOTHING
        """)
    )

    # ── Category ─────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            INSERT INTO categories (id, name, slug, description, enabled, display_order)
            VALUES (:id, 'Food Products', 'food_products',
                    'Manufactured food and beverage products for sale in Sri Lanka.', :enabled, 1)
            ON CONFLICT (slug) DO NOTHING
        """),
        {"id": CAT_FOOD_PRODUCTS, "enabled": True},
    )

    # ── Product ───────────────────────────────────────────────────────────────
    conn.execute(
        sa.text("""
            INSERT INTO products (id, category_id, name, slug, description, enabled, display_order)
            VALUES (:id, :cat_id, 'Fresh Fruit Cordial', 'fresh_fruit_cordial',
                    'A sweetened, dilutable fruit drink concentrate made from fresh fruit juice, sugar, water, and permitted preservatives.',
                    :enabled, 1)
            ON CONFLICT (slug) DO NOTHING
        """),
        {"id": PROD_CORDIAL, "cat_id": CAT_FOOD_PRODUCTS, "enabled": True},
    )

    # ── Certification schemes ─────────────────────────────────────────────────
    # SLS Mark — Product Quality track
    sls_weights = {
        "Hygiene & Sanitation": 20,
        "Process Control": 20,
        "Documentation & Records": 15,
        "Raw Material & Supplier Control": 15,
        "Packaging & Labelling": 15,
        "Storage & Traceability": 15,
    }
    conn.execute(
        sa.text("""
            INSERT INTO certification_schemes
              (id, name, short_code, track, body_id, product_id, mandatory_tier,
               applicability_rule, category_weights, summary, typical_timeline_days,
               source_url, active, display_order)
            VALUES
              ('SLS_MARK_CORDIAL', 'SLS Mark — Fresh Fruit Cordial', 'SLS_MARK',
               'product_quality', 'SLSI', :prod_id, 'market_required',
               :app_rule, :cat_weights,
               'The SLS Mark certifies that your product consistently meets the Sri Lanka Standard for Fresh Fruit Cordial (SLS 187). It is widely required by supermarkets and institutional buyers.',
               365, 'https://www.slsi.lk/product-certification.html', :active, 1)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "prod_id": PROD_CORDIAL,
            "app_rule": '{"market": ["supermarket", "export", "institutional"], "mandatory_note": "Required by most supermarket chains and all government institutional buyers."}',
            "cat_weights": str(sls_weights).replace("'", '"'),
            "active": True,
        },
    )

    # CAA Registration — mandatory by law
    caa_weights = {
        "Labelling Compliance": 40,
        "Product Standards": 30,
        "Business Registration": 30,
    }
    conn.execute(
        sa.text("""
            INSERT INTO certification_schemes
              (id, name, short_code, track, body_id, product_id, mandatory_tier,
               applicability_rule, category_weights, summary, typical_timeline_days,
               source_url, active, display_order)
            VALUES
              ('CAA_FOOD_REG', 'CAA Food Business Registration', 'CAA_REG',
               'product_quality', 'CAA', :prod_id, 'mandatory',
               :app_rule, :cat_weights,
               'Mandatory registration under the Consumer Affairs Authority Act and Food Act No. 26 of 1980. Required before any food product can be legally sold in Sri Lanka.',
               60, 'https://www.caa.gov.lk', :active, 2)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "prod_id": PROD_CORDIAL,
            "app_rule": '{"mandatory_note": "Required by law for all food manufacturers selling in Sri Lanka (Food Act No. 26 of 1980)."}',
            "cat_weights": str(caa_weights).replace("'", '"'),
            "active": True,
        },
    )

    # ISO 22000 — disabled (future)
    conn.execute(
        sa.text("""
            INSERT INTO certification_schemes
              (id, name, short_code, track, body_id, product_id, mandatory_tier,
               applicability_rule, category_weights, summary, typical_timeline_days,
               source_url, active, display_order)
            VALUES
              ('ISO_22000', 'ISO 22000 Food Safety Management', 'ISO_22000',
               'process_management', 'ISO', NULL, 'optional',
               :app_rule, '{}',
               'International food safety management system standard. Typically required for export to regulated markets. Coming soon in CertifyLK.',
               540, 'https://www.iso.org/iso-22000-food-safety-management.html', :active, 1)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "app_rule": '{"market": ["export"], "note": "Required for EU/US export markets."}',
            "active": False,
        },
    )

    # ── SLS Mark requirements (content_verified=False, draft) ─────────────────
    def req(
        rid: str,
        cat: str,
        title: str,
        desc: str,
        weight: float,
        safety: bool,
        doc: str,
        clause: str,
        rule: str,
        order: int,
    ) -> None:
        conn.execute(
            sa.text("""
                INSERT INTO scheme_requirements
                  (id, scheme_id, category_label, title, description, weight,
                   safety_critical, source_document, clause_reference, source_url,
                   content_verified, evaluation_rule, display_order, active)
                VALUES
                  (:id, 'SLS_MARK_CORDIAL', :cat, :title, :desc, :weight,
                   :safety, :doc, :clause, '', :content_verified, :rule, :order, :active)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": rid,
                "cat": cat,
                "title": title,
                "desc": desc,
                "weight": weight,
                "safety": safety,
                "doc": doc,
                "clause": clause,
                "content_verified": False,
                "rule": rule,
                "order": order,
                "active": True,
            },
        )

    # Hygiene & Sanitation (weight total: 20)
    req(
        "SLS_HYG_HANDWASH",
        "Hygiene & Sanitation",
        "Handwashing facilities and supplies",
        "Suitable handwashing facilities with soap and hygienic drying must be accessible to all production staff at all times.",
        6,
        True,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 4.2.1 — Personal Hygiene",
        '{"question": "HYG_HAND_01", "confirmed": ["always"], "partial": ["sometimes"], "gap": ["never"]}',
        1,
    )

    req(
        "SLS_HYG_CLEANING",
        "Hygiene & Sanitation",
        "Defined cleaning and sanitising programme",
        "All food-contact surfaces, equipment, and utensils must follow a documented cleaning and sanitising schedule.",
        6,
        True,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 4.3.1 — Cleaning Programme",
        '{"question": "HYG_CLEAN_01", "confirmed": ["recorded_each_batch"], "partial": ["routine_no_record"], "gap": ["only_when_dirty"]}',
        2,
    )

    req(
        "SLS_HYG_CHEMICAL",
        "Hygiene & Sanitation",
        "Cleaning chemicals labelled and separated",
        "Cleaning chemicals must be correctly labelled, stored separately from food ingredients, and used according to supplier instructions.",
        4,
        True,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 4.3.3 — Chemical Control",
        '{"question": "HYG_CHEM_01", "confirmed": ["locked_separate"], "partial": ["separate_area"], "gap": ["with_ingredients"]}',
        3,
    )

    req(
        "SLS_HYG_PEST",
        "Hygiene & Sanitation",
        "Pest control and monitoring",
        "A documented pest monitoring and control programme must be in place. Evidence of pest activity must be recorded and acted upon.",
        4,
        False,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 4.4 — Pest Control",
        '{"question": "HYG_PEST_01", "confirmed": ["logged"], "partial": ["checked_not_logged"], "gap": ["not_checked"]}',
        4,
    )

    # Process Control (weight total: 20)
    req(
        "SLS_PROC_STAGES",
        "Process Control",
        "Documented production stages",
        "The manufacturer must be able to describe and demonstrate all critical production stages from raw material receipt to finished product dispatch.",
        5,
        False,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 5.1 — Process Definition",
        '{"derived": "process_steps"}',
        5,
    )

    req(
        "SLS_PROC_TEMP",
        "Process Control",
        "Thermal processing control (cooking endpoint)",
        "For products requiring heat treatment, a repeatable, measured endpoint (time/temperature) must be defined and recorded for each batch.",
        7,
        True,
        "SLS 187",
        "Clause 5.3.2 — Thermal Process Control",
        '{"question": "PROC_TEMP_01", "confirmed": ["thermometer"], "partial": ["time_and_appearance"], "gap": ["appearance_only"]}',
        6,
    )

    req(
        "SLS_PROC_FILL",
        "Process Control",
        "Protected filling and container closure",
        "Containers must be filled and sealed in a manner that prevents contamination. Hot-fill or post-fill pasteurisation must be validated.",
        4,
        True,
        "SLS 187",
        "Clause 5.4 — Filling and Closing",
        '{"question": "PACK_FILL_01", "confirmed": ["dedicated_clean_area"], "partial": ["cleaned_shared_area"], "gap": ["uncontrolled_area"]}',
        7,
    )

    req(
        "SLS_PROC_SEP",
        "Process Control",
        "Separation of raw and finished product areas",
        "Cross-contamination between raw materials and finished product must be prevented through physical separation or time-based scheduling.",
        4,
        True,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 5.2 — Cross-contamination Prevention",
        '{"question": "PROC_SEP_01", "confirmed": ["separate_time_area"], "partial": ["clean_between"], "gap": ["same_without_cleaning"]}',
        8,
    )

    # Documentation & Records (weight total: 15)
    req(
        "SLS_DOC_BATCH",
        "Documentation & Records",
        "Batch production records",
        "A batch record must be completed for every production run, capturing date, ingredients used (with lot references), process parameters, output quantities, and responsible person.",
        6,
        False,
        "SLS 187",
        "Clause 7.1 — Batch Records",
        '{"question": "DOC_BATCH_01", "confirmed": ["always"], "partial": ["sometimes"], "gap": ["never"]}',
        9,
    )

    req(
        "SLS_DOC_CLEANING",
        "Documentation & Records",
        "Cleaning records",
        "Cleaning activities must be recorded with date, area/equipment cleaned, cleaning agent used, and responsible person.",
        5,
        False,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 7.2 — Cleaning Records",
        '{"question": "DOC_CLEAN_01", "confirmed": ["every_day"], "partial": ["sometimes"], "gap": ["never"]}',
        10,
    )

    req(
        "SLS_DOC_COMPLAINT",
        "Documentation & Records",
        "Customer complaint records",
        "All customer complaints related to product quality or safety must be recorded and investigated. A corrective action must be documented.",
        4,
        False,
        "SLS 187",
        "Clause 7.4 — Complaint Handling",
        '{"question": "DOC_COMPLAINT_01", "confirmed": ["always"], "partial": ["sometimes"], "gap": ["never"]}',
        11,
    )

    # Raw Material & Supplier Control (weight total: 15)
    req(
        "SLS_SUP_SOURCE",
        "Raw Material & Supplier Control",
        "Approved supplier programme",
        "Fruit juice or concentrate, sugar, water, and permitted preservatives must be sourced from identifiable, consistent suppliers. An approved supplier list must be maintained.",
        6,
        True,
        "SLS 187",
        "Clause 6.1 — Raw Material Sourcing",
        '{"question": "SUP_SOURCE_01", "confirmed": ["approved_regular"], "partial": ["known_variable"], "gap": ["unknown_cash"]}',
        12,
    )

    req(
        "SLS_SUP_REGISTER",
        "Raw Material & Supplier Control",
        "Supplier register",
        "A register of all suppliers including name, contact, and ingredients supplied must be maintained and kept current.",
        5,
        False,
        "SLS 187 / GMP Guidelines (SLSI)",
        "Clause 6.2 — Supplier Register",
        '{"question": "SUP_REG_01", "confirmed": ["complete"], "partial": ["informal"], "gap": ["none"]}',
        13,
    )

    req(
        "SLS_SUP_INCOMING",
        "Raw Material & Supplier Control",
        "Incoming raw material inspection",
        "All incoming raw materials must be inspected for condition, quantity, and labelling. Non-conforming materials must be rejected and the event recorded.",
        4,
        False,
        "SLS 187",
        "Clause 6.3 — Incoming Inspection",
        '{"question": "SUP_CHECK_01", "confirmed": ["check_record"], "partial": ["check_no_record"], "gap": ["no_check"]}',
        14,
    )

    # Packaging & Labelling (weight total: 15)
    req(
        "SLS_PACK_LABEL",
        "Packaging & Labelling",
        "Label conformance to SLS 187 and Food Act",
        "The finished product label must declare: product name, list of ingredients (in descending order), net contents, best-before date, batch/lot code, manufacturer name and address, storage instructions, and permitted additives with INS numbers.",
        7,
        False,
        "Food Act No. 26 of 1980 / SLS 187",
        "Clause 9 — Labelling Requirements",
        '{"question": "PACK_LABEL_01", "confirmed": ["complete"], "partial": ["some_details"], "gap": ["name_only"]}',
        15,
    )

    req(
        "SLS_PACK_FOODGRADE",
        "Packaging & Labelling",
        "Food-grade packaging evidence",
        "Primary packaging must be food-grade, inert, and suitable for the product. A supplier declaration or specification confirming food-grade status must be retained.",
        5,
        False,
        "SLS 187",
        "Clause 8.1 — Packaging Materials",
        '{"question": "PACK_GRADE_01", "confirmed": ["documented"], "partial": ["supplier_statement"], "gap": ["none"]}',
        16,
    )

    req(
        "SLS_PACK_SHELF",
        "Packaging & Labelling",
        "Best-before date — supported shelf life",
        "The declared best-before date must be supported by shelf-life data (accelerated or real-time testing) or documented advice from a competent authority.",
        3,
        False,
        "Food Act No. 26 of 1980 / SLS 187",
        "Clause 9.4 — Date Marking",
        '{"question": "PACK_DATE_01", "confirmed": ["supported"], "partial": ["experience"], "gap": ["none"]}',
        17,
    )

    # Storage & Traceability (weight total: 15)
    req(
        "SLS_STORE_INGREDIENT",
        "Storage & Traceability",
        "Ingredient storage — raised, covered, and labelled",
        "All raw materials must be stored off the floor, in closed containers, away from walls and protected from contamination. Storage areas must be clean and dry.",
        4,
        False,
        "GMP Guidelines (SLSI)",
        "Clause 4.5 — Ingredient Storage",
        '{"question": "STORE_RAISED_01", "confirmed": ["raised_closed"], "partial": ["raised_open"], "gap": ["on_floor"]}',
        18,
    )

    req(
        "SLS_STORE_FINISHED",
        "Storage & Traceability",
        "Finished product storage conditions",
        "Finished products must be stored under conditions (temperature, humidity) specified on the label. Products must be protected from contamination.",
        3,
        False,
        "SLS 187",
        "Clause 5.5 — Finished Product Storage",
        '{"question": "STORE_FIN_01", "confirmed": ["separate_protected"], "partial": ["shared_protected"], "gap": ["unprotected"]}',
        19,
    )

    req(
        "SLS_TRACE_BATCH",
        "Storage & Traceability",
        "Batch code on finished product",
        "Every finished product unit must be labelled with a batch/lot code that links it to the corresponding batch production record.",
        5,
        False,
        "SLS 187",
        "Clause 7.1.4 — Batch Identification",
        '{"question": "TRACE_CODE_01", "confirmed": ["every_batch"], "partial": ["date_only"], "gap": ["none"]}',
        20,
    )

    req(
        "SLS_TRACE_DIST",
        "Storage & Traceability",
        "Distribution traceability records",
        "The destination of each batch (customer, outlet, or market) must be recorded to enable product recall within 24 hours if required.",
        3,
        False,
        "SLS 187",
        "Clause 7.3 — Distribution Records",
        '{"question": "TRACE_SALES_01", "confirmed": ["batch_customer"], "partial": ["sales_only"], "gap": ["none"]}',
        21,
    )

    # ── SLS Mark cost items ───────────────────────────────────────────────────
    def cost(
        cid: str,
        aref: str,
        title: str,
        ctype: str,
        ot_min: int,
        ot_max: int,
        rec_min: int,
        rec_max: int,
        note: str,
    ) -> None:
        conn.execute(
            sa.text("""
                INSERT INTO scheme_cost_items
                  (id, scheme_id, action_ref, title, cost_type,
                   one_time_min, one_time_max, recurring_min, recurring_max,
                   currency, source_note, effective_date, last_reviewed)
                VALUES
                  (:id, 'SLS_MARK_CORDIAL', :aref, :title, :ctype,
                   :ot_min, :ot_max, :rec_min, :rec_max,
                   'LKR', :note, :eff, :rev)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": cid,
                "aref": aref,
                "title": title,
                "ctype": ctype,
                "ot_min": ot_min,
                "ot_max": ot_max,
                "rec_min": rec_min,
                "rec_max": rec_max,
                "note": note,
                "eff": EFFECTIVE,
                "rev": REVIEWED,
            },
        )

    cost(
        "COST_SLS_APP_FEE",
        "SLS_APPLICATION",
        "SLSI Application and Certification Fee",
        "certifying_body_fee",
        50000,
        150000,
        25000,
        75000,
        "SLSI fee schedule (estimate, 2024). Varies by production volume and product complexity. Contact SLSI for exact quote.",
    )

    cost(
        "COST_LAB_INITIAL",
        "SLS_LAB_TESTING",
        "Laboratory testing — initial certification",
        "lab_testing_fee",
        75000,
        200000,
        0,
        0,
        "Includes physicochemical (Brix, pH, preservative level) and microbial testing at SLSI-accredited laboratory. Ongoing surveillance testing billed separately.",
    )

    cost(
        "COST_LAB_ANNUAL",
        "SLS_LAB_ANNUAL",
        "Annual surveillance laboratory testing",
        "lab_testing_fee",
        30000,
        80000,
        30000,
        80000,
        "Annual product testing required to maintain SLS Mark. Frequency and scope determined by SLSI auditor.",
    )

    cost(
        "COST_DOC_SETUP",
        "SLS_DOC_SETUP",
        "Documentation system setup (batch records, cleaning logs)",
        "business_capex",
        0,
        5000,
        0,
        1500,
        "Printing and stationery for paper-based records, or spreadsheet templates. Staff time excluded.",
    )

    cost(
        "COST_LABEL_REDESIGN",
        "SLS_LABEL_REDESIGN",
        "Label redesign to meet SLS 187 and Food Act requirements",
        "business_capex",
        15000,
        75000,
        0,
        0,
        "Graphic design and printing of updated labels. Cost depends on label complexity and print run size.",
    )

    cost(
        "COST_THERMOMETER",
        "SLS_THERMOMETER",
        "Food-grade calibrated thermometer",
        "business_capex",
        3000,
        12000,
        0,
        1500,
        "Food-grade probe thermometer. Annual calibration recommended.",
    )

    cost(
        "COST_PEST_CONTRACT",
        "SLS_PEST_CONTROL",
        "Professional pest control contract",
        "business_opex",
        0,
        0,
        12000,
        48000,
        "Annual pest control service from a licensed provider. Cost varies by facility size and pest risk level.",
    )

    cost(
        "COST_SLSI_AUDIT",
        "SLS_AUDIT",
        "SLSI on-site factory assessment",
        "certifying_body_fee",
        0,
        0,
        15000,
        50000,
        "Annual SLSI factory audit fee (included in some annual certification packages, charged separately in others).",
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM scheme_cost_items WHERE scheme_id LIKE 'SLS_%' OR scheme_id LIKE 'CAA_%' OR scheme_id LIKE 'ISO_%'"
        )
    )
    conn.execute(
        sa.text(
            "DELETE FROM scheme_requirements WHERE scheme_id LIKE 'SLS_%' OR scheme_id LIKE 'CAA_%'"
        )
    )
    conn.execute(
        sa.text(
            "DELETE FROM certification_schemes WHERE id IN ('SLS_MARK_CORDIAL', 'CAA_FOOD_REG', 'ISO_22000')"
        )
    )
    conn.execute(sa.text("DELETE FROM certification_bodies WHERE id IN ('SLSI', 'CAA', 'ISO')"))
    conn.execute(sa.text(f"DELETE FROM products WHERE id = '{PROD_CORDIAL}'"))
    conn.execute(sa.text(f"DELETE FROM categories WHERE id = '{CAT_FOOD_PRODUCTS}'"))
