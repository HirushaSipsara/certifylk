import uuid
from datetime import date
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from app.data.catalog import (
    CATALOGUE_REVIEW_DATE,
    QUESTION_BANK,
    RECOMMENDATIONS,
    REQUIREMENTS,
)
from app.models import (
    Category,
    CertificationBody,
    CertificationScheme,
    CostItem,
    Product,
    QuestionBank,
    Recommendation,
    Requirement,
    SchemeCostItem,
    SchemeRequirement,
)
from app.models.enums import CertificationTrack, CostType, MandatoryTier, RequirementCategory

CAT_FOOD_PRODUCTS = uuid.UUID("11111111-1111-1111-1111-111111111111")
PROD_CORDIAL = uuid.UUID("22222222-2222-2222-2222-222222222222")
REVIEWED = date(2026, 8, 7)


def seed_catalogue(db: Session) -> dict[str, int]:
    for item in REQUIREMENTS:
        db.merge(
            Requirement(
                id=str(item["id"]),
                category=RequirementCategory(str(item["category"])),
                title=str(item["title"]),
                description=str(item["description"]),
                weight=Decimal(str(item["weight"])),
                safety_critical=bool(item["safety_critical"]),
                applicability_tags=cast(list[str], item.get("applicability_tags", [])),
                evaluation_rule=cast(dict[str, Any], item["evaluation_rule"]),
                active=True,
            )
        )

    for item in QUESTION_BANK:
        db.merge(
            QuestionBank(
                id=str(item["id"]),
                category=str(item["category"]),
                text=str(item["text"]),
                options=cast(list[dict[str, str]], item["options"]),
                allows_other=bool(item["allows_other"]),
                product_tags=cast(list[str], item["product_tags"]),
                process_tags=cast(list[str], item["process_tags"]),
                requirement_ids=cast(list[str], item["requirement_ids"]),
                priority=cast(int, item["priority"]),
                page_eligibility=cast(list[str], item["page_eligibility"]),
                active=True,
            )
        )

    for (
        rec_id,
        title,
        steps,
        requirement_ids,
        priority,
        is_capex,
        one_min,
        one_max,
        recurring_min,
        recurring_max,
        note,
    ) in RECOMMENDATIONS:
        db.merge(
            Recommendation(
                id=rec_id,
                title=title,
                implementation_steps=steps,
                requirement_ids=requirement_ids,
                priority_base=priority,
                is_capex=is_capex,
                cost_note=note,
                last_reviewed=CATALOGUE_REVIEW_DATE,
                active=True,
            )
        )
        db.merge(
            CostItem(
                id=f"COST_{rec_id}",
                recommendation_id=rec_id,
                one_time_min=one_min,
                one_time_max=one_max,
                recurring_min=recurring_min,
                recurring_max=recurring_max,
                currency="LKR",
                effective_date=CATALOGUE_REVIEW_DATE,
                last_reviewed=CATALOGUE_REVIEW_DATE,
            )
        )

    # ── Certification Knowledge Base ──────────────────────────────────────────
    bodies = [
        (
            "SLSI",
            "Sri Lanka Standards Institution",
            "SLSI",
            "https://www.slsi.lk",
            "Government body responsible for standardisation and product certification in Sri Lanka.",
        ),
        (
            "CAA",
            "Consumer Affairs Authority",
            "CAA",
            "https://www.caa.gov.lk",
            "Statutory body regulating food labelling and consumer protection in Sri Lanka.",
        ),
        (
            "ISO",
            "International Organization for Standardization",
            "ISO",
            "https://www.iso.org",
            "International standards body — ISO 22000 Food Safety Management Systems.",
        ),
    ]
    for bid, bname, bcode, burl, bdesc in bodies:
        db.merge(
            CertificationBody(
                id=bid, name=bname, short_code=bcode, website_url=burl, description=bdesc
            )
        )

    cat_food = Category(
        id=CAT_FOOD_PRODUCTS,
        name="Food Products",
        slug="food_products",
        description="Manufactured food and beverage products for sale in Sri Lanka.",
        enabled=True,
        display_order=1,
    )
    db.merge(cat_food)

    prod_cordial = Product(
        id=PROD_CORDIAL,
        category_id=CAT_FOOD_PRODUCTS,
        name="Fresh Fruit Cordial",
        slug="fresh_fruit_cordial",
        description="A sweetened, dilutable fruit drink concentrate made from fresh fruit juice, sugar, water, and permitted preservatives.",
        enabled=True,
        display_order=1,
    )
    db.merge(prod_cordial)

    sls_weights = {
        "Hygiene & Sanitation": 20,
        "Process Control": 20,
        "Documentation & Records": 15,
        "Raw Material & Supplier Control": 15,
        "Packaging & Labelling": 15,
        "Storage & Traceability": 15,
    }
    db.merge(
        CertificationScheme(
            id="SLS_MARK_CORDIAL",
            name="SLS Mark — Fresh Fruit Cordial",
            short_code="SLS_MARK",
            track=CertificationTrack.PRODUCT_QUALITY,
            body_id="SLSI",
            product_id=PROD_CORDIAL,
            mandatory_tier=MandatoryTier.MARKET_REQUIRED,
            applicability_rule={
                "market": ["supermarket", "export", "institutional"],
                "mandatory_note": "Required by most supermarket chains and all government institutional buyers.",
            },
            category_weights=sls_weights,
            summary="The SLS Mark certifies that your product consistently meets the Sri Lanka Standard for Fresh Fruit Cordial (SLS 187). It is widely required by supermarkets and institutional buyers.",
            typical_timeline_days=365,
            source_url="https://www.slsi.lk/product-certification.html",
            active=True,
            display_order=1,
        )
    )

    caa_weights = {
        "Labelling Compliance": 40,
        "Product Standards": 30,
        "Business Registration": 30,
    }
    db.merge(
        CertificationScheme(
            id="CAA_FOOD_REG",
            name="CAA Food Business Registration",
            short_code="CAA_REG",
            track=CertificationTrack.PRODUCT_QUALITY,
            body_id="CAA",
            product_id=PROD_CORDIAL,
            mandatory_tier=MandatoryTier.MANDATORY,
            applicability_rule={
                "mandatory_note": "Required by law for all food manufacturers selling in Sri Lanka (Food Act No. 26 of 1980)."
            },
            category_weights=caa_weights,
            summary="Mandatory registration under the Consumer Affairs Authority Act and Food Act No. 26 of 1980. Required before any food product can be legally sold in Sri Lanka.",
            typical_timeline_days=60,
            source_url="https://www.caa.gov.lk",
            active=True,
            display_order=2,
        )
    )

    db.merge(
        CertificationScheme(
            id="ISO_22000",
            name="ISO 22000 Food Safety Management",
            short_code="ISO_22000",
            track=CertificationTrack.PROCESS_MANAGEMENT,
            body_id="ISO",
            product_id=None,
            mandatory_tier=MandatoryTier.OPTIONAL,
            applicability_rule={"market": ["export"], "note": "Required for EU/US export markets."},
            category_weights={},
            summary="International food safety management system standard. Typically required for export to regulated markets. Coming soon in CertifyLK.",
            typical_timeline_days=540,
            source_url="https://www.iso.org/iso-22000-food-safety-management.html",
            active=False,
            display_order=1,
        )
    )

    # 21 SLS Mark Requirements
    sls_req_data = [
        (
            "SLS_HYG_HANDWASH",
            "Hygiene & Sanitation",
            "Handwashing facilities and supplies",
            "Suitable handwashing facilities with soap and hygienic drying must be accessible to all production staff at all times.",
            6.0,
            True,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 4.2.1 — Personal Hygiene",
            1,
        ),
        (
            "SLS_HYG_CLEANING",
            "Hygiene & Sanitation",
            "Defined cleaning and sanitising programme",
            "All food-contact surfaces, equipment, and utensils must follow a documented cleaning and sanitising schedule.",
            6.0,
            True,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 4.3.1 — Cleaning Programme",
            2,
        ),
        (
            "SLS_HYG_CHEMICAL",
            "Hygiene & Sanitation",
            "Cleaning chemicals labelled and separated",
            "Cleaning chemicals must be correctly labelled, stored separately from food ingredients, and used according to supplier instructions.",
            4.0,
            True,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 4.3.3 — Chemical Control",
            3,
        ),
        (
            "SLS_HYG_PEST",
            "Hygiene & Sanitation",
            "Pest control and monitoring",
            "A documented pest monitoring and control programme must be in place. Evidence of pest activity must be recorded and acted upon.",
            4.0,
            False,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 4.4 — Pest Control",
            4,
        ),
        (
            "SLS_PROC_STAGES",
            "Process Control",
            "Documented production stages",
            "The manufacturer must be able to describe and demonstrate all critical production stages from raw material receipt to finished product dispatch.",
            5.0,
            False,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 5.1 — Process Definition",
            5,
        ),
        (
            "SLS_PROC_TEMP",
            "Process Control",
            "Thermal processing control (cooking endpoint)",
            "For products requiring heat treatment, a repeatable, measured endpoint (time/temperature) must be defined and recorded for each batch.",
            7.0,
            True,
            "SLS 187",
            "Clause 5.3.2 — Thermal Process Control",
            6,
        ),
        (
            "SLS_PROC_FILL",
            "Process Control",
            "Protected filling and container closure",
            "Containers must be filled and sealed in a manner that prevents contamination. Hot-fill or post-fill pasteurisation must be validated.",
            4.0,
            True,
            "SLS 187",
            "Clause 5.4 — Filling and Closing",
            7,
        ),
        (
            "SLS_PROC_SEP",
            "Process Control",
            "Separation of raw and finished product areas",
            "Cross-contamination between raw materials and finished product must be prevented through physical separation or time-based scheduling.",
            4.0,
            True,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 5.2 — Cross-contamination Prevention",
            8,
        ),
        (
            "SLS_DOC_BATCH",
            "Documentation & Records",
            "Batch production records",
            "A batch record must be completed for every production run, capturing date, ingredients used (with lot references), process parameters, output quantities, and responsible person.",
            6.0,
            False,
            "SLS 187",
            "Clause 7.1 — Batch Records",
            9,
        ),
        (
            "SLS_DOC_CLEANING",
            "Documentation & Records",
            "Cleaning records",
            "Cleaning activities must be recorded with date, area/equipment cleaned, cleaning agent used, and responsible person.",
            5.0,
            False,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 7.2 — Cleaning Records",
            10,
        ),
        (
            "SLS_DOC_COMPLAINT",
            "Documentation & Records",
            "Customer complaint records",
            "All customer complaints related to product quality or safety must be recorded and investigated. A corrective action must be documented.",
            4.0,
            False,
            "SLS 187",
            "Clause 7.4 — Complaint Handling",
            11,
        ),
        (
            "SLS_SUP_SOURCE",
            "Raw Material & Supplier Control",
            "Approved supplier programme",
            "Fruit juice or concentrate, sugar, water, and permitted preservatives must be sourced from identifiable, consistent suppliers. An approved supplier list must be maintained.",
            6.0,
            True,
            "SLS 187",
            "Clause 6.1 — Raw Material Sourcing",
            12,
        ),
        (
            "SLS_SUP_REGISTER",
            "Raw Material & Supplier Control",
            "Supplier register",
            "A register of all suppliers including name, contact, and ingredients supplied must be maintained and kept current.",
            5.0,
            False,
            "SLS 187 / GMP Guidelines (SLSI)",
            "Clause 6.2 — Supplier Register",
            13,
        ),
        (
            "SLS_SUP_INCOMING",
            "Raw Material & Supplier Control",
            "Incoming raw material inspection",
            "All incoming raw materials must be inspected for condition, quantity, and labelling. Non-conforming materials must be rejected and the event recorded.",
            4.0,
            False,
            "SLS 187",
            "Clause 6.3 — Incoming Inspection",
            14,
        ),
        (
            "SLS_PACK_LABEL",
            "Packaging & Labelling",
            "Label conformance to SLS 187 and Food Act",
            "The finished product label must declare: product name, list of ingredients (in descending order), net contents, best-before date, batch/lot code, manufacturer name and address, storage instructions, and permitted additives with INS numbers.",
            7.0,
            False,
            "Food Act No. 26 of 1980 / SLS 187",
            "Clause 9 — Labelling Requirements",
            15,
        ),
        (
            "SLS_PACK_FOODGRADE",
            "Packaging & Labelling",
            "Food-grade packaging evidence",
            "Primary packaging must be food-grade, inert, and suitable for the product. A supplier declaration or specification confirming food-grade status must be retained.",
            5.0,
            False,
            "SLS 187",
            "Clause 8.1 — Packaging Materials",
            16,
        ),
        (
            "SLS_PACK_SHELF",
            "Packaging & Labelling",
            "Best-before date — supported shelf life",
            "The declared best-before date must be supported by shelf-life data (accelerated or real-time testing) or documented advice from a competent authority.",
            3.0,
            False,
            "Food Act No. 26 of 1980 / SLS 187",
            "Clause 9.4 — Date Marking",
            17,
        ),
        (
            "SLS_STORE_INGREDIENT",
            "Storage & Traceability",
            "Ingredient storage — raised, covered, and labelled",
            "All raw materials must be stored off the floor, in closed containers, away from walls and protected from contamination. Storage areas must be clean and dry.",
            4.0,
            False,
            "GMP Guidelines (SLSI)",
            "Clause 4.5 — Ingredient Storage",
            18,
        ),
        (
            "SLS_STORE_FINISHED",
            "Storage & Traceability",
            "Finished product storage conditions",
            "Finished products must be stored under conditions (temperature, humidity) specified on the label. Products must be protected from contamination.",
            3.0,
            False,
            "SLS 187",
            "Clause 5.5 — Finished Product Storage",
            19,
        ),
        (
            "SLS_TRACE_BATCH",
            "Storage & Traceability",
            "Batch code on finished product",
            "Every finished product unit must be labelled with a batch/lot code that links it to the corresponding batch production record.",
            5.0,
            False,
            "SLS 187",
            "Clause 7.1.4 — Batch Identification",
            20,
        ),
        (
            "SLS_TRACE_DIST",
            "Storage & Traceability",
            "Distribution traceability records",
            "The destination of each batch (customer, outlet, or market) must be recorded to enable product recall within 24 hours if required.",
            3.0,
            False,
            "SLS 187",
            "Clause 7.3 — Distribution Records",
            21,
        ),
    ]

    for rid, cat_lbl, title, desc, w, safety, sdoc, sclause, dorder in sls_req_data:
        db.merge(
            SchemeRequirement(
                id=rid,
                scheme_id="SLS_MARK_CORDIAL",
                category_label=cat_lbl,
                title=title,
                description=desc,
                weight=Decimal(str(w)),
                safety_critical=safety,
                source_document=sdoc,
                clause_reference=sclause,
                source_url="",
                content_verified=False,
                evaluation_rule={},
                display_order=dorder,
                active=True,
            )
        )

    # 8 Cost items
    cost_items = [
        (
            "COST_SLS_APP_FEE",
            "SLS_APPLICATION",
            "SLSI Application and Certification Fee",
            CostType.CERTIFYING_BODY_FEE,
            50000,
            150000,
            25000,
            75000,
            "SLSI fee schedule (estimate, 2024). Varies by production volume and product complexity.",
        ),
        (
            "COST_LAB_INITIAL",
            "SLS_LAB_TESTING",
            "Laboratory testing — initial certification",
            CostType.LAB_TESTING_FEE,
            75000,
            200000,
            0,
            0,
            "Includes physicochemical and microbial testing at SLSI-accredited laboratory.",
        ),
        (
            "COST_LAB_ANNUAL",
            "SLS_LAB_ANNUAL",
            "Annual surveillance laboratory testing",
            CostType.LAB_TESTING_FEE,
            30000,
            80000,
            30000,
            80000,
            "Annual product testing required to maintain SLS Mark.",
        ),
        (
            "COST_DOC_SETUP",
            "SLS_DOC_SETUP",
            "Documentation system setup (batch records, cleaning logs)",
            CostType.BUSINESS_CAPEX,
            0,
            5000,
            0,
            1500,
            "Printing and stationery for paper-based records.",
        ),
        (
            "COST_LABEL_REDESIGN",
            "SLS_LABEL_REDESIGN",
            "Label redesign to meet SLS 187 and Food Act requirements",
            CostType.BUSINESS_CAPEX,
            15000,
            75000,
            0,
            0,
            "Graphic design and printing of updated labels.",
        ),
        (
            "COST_THERMOMETER",
            "SLS_THERMOMETER",
            "Food-grade calibrated thermometer",
            CostType.BUSINESS_CAPEX,
            3000,
            12000,
            0,
            1500,
            "Food-grade probe thermometer.",
        ),
        (
            "COST_PEST_CONTRACT",
            "SLS_PEST_CONTROL",
            "Professional pest control contract",
            CostType.BUSINESS_OPEX,
            0,
            0,
            12000,
            48000,
            "Annual pest control service from a licensed provider.",
        ),
        (
            "COST_SLSI_AUDIT",
            "SLS_AUDIT",
            "SLSI on-site factory assessment",
            CostType.CERTIFYING_BODY_FEE,
            0,
            0,
            15000,
            50000,
            "Annual SLSI factory audit fee.",
        ),
    ]

    for cid, aref, title, ctype, ot_min, ot_max, rec_min, rec_max, note in cost_items:
        db.merge(
            SchemeCostItem(
                id=cid,
                scheme_id="SLS_MARK_CORDIAL",
                action_ref=aref,
                title=title,
                cost_type=ctype,
                one_time_min=ot_min,
                one_time_max=ot_max,
                recurring_min=rec_min,
                recurring_max=rec_max,
                currency="LKR",
                source_note=note,
                effective_date=REVIEWED,
                last_reviewed=REVIEWED,
            )
        )

    db.commit()
    return {
        "requirements": len(REQUIREMENTS),
        "questions": len(QUESTION_BANK),
        "recommendations": len(RECOMMENDATIONS),
    }
