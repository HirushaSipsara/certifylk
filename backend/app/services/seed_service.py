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
    db.flush()

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
    db.flush()

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

    # ── Phase 2 — Track 2: Process & System Certification ────────────────────

    # Category for process management track
    cat_process = Category(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        name="Process & System Certification",
        slug="process_management",
        description="Management system certifications for food safety, hygiene, and export market access.",
        enabled=True,
        display_order=2,
    )
    db.merge(cat_process)

    # ── SLS GMP Certification ─────────────────────────────────────────────────
    gmp_weights = {
        "Premises & Facilities": 20,
        "Personnel Hygiene": 15,
        "Equipment & Maintenance": 15,
        "Water & Utilities": 10,
        "Production Controls": 15,
        "Pest & Waste Control": 10,
        "Documentation & Records": 15,
    }
    db.merge(
        CertificationScheme(
            id="SLS_GMP",
            name="SLS GMP Certification",
            short_code="GMP",
            track=CertificationTrack.PROCESS_MANAGEMENT,
            body_id="SLSI",
            product_id=None,
            mandatory_tier=MandatoryTier.RECOMMENDED,
            applicability_rule={
                "note": "Recommended for all food manufacturers. Required by most supermarket chains as a baseline prerequisite alongside SLS Mark certification."
            },
            category_weights=gmp_weights,
            summary="SLSI-issued Good Manufacturing Practice certification. Demonstrates systematic control of food production premises, personnel, equipment, and processes. Widely recognised as the foundation for food safety in Sri Lanka.",
            typical_timeline_days=180,
            source_url="https://www.slsi.lk/product-certification.html",
            active=True,
            display_order=1,
        )
    )
    db.flush()  # ensure scheme row is written before FK-dependent children

    gmp_reqs = [
        ("GMP_PREM_DESIGN", "Premises & Facilities", "Hygienic facility design and layout", "Production areas must be designed to prevent contamination. Traffic flows must separate raw material receipt, processing, packaging, and dispatch. Floors, walls, and ceilings must be of smooth, cleanable construction.", 7.0, False, "SLSI GMP Guidelines", "Section 3.1 — Premises Design", 1),
        ("GMP_PREM_LIGHT", "Premises & Facilities", "Adequate lighting in production areas", "All food preparation, inspection, and storage areas must have adequate, safe lighting. Light fittings above open food must be shatter-resistant or shielded.", 4.0, False, "SLSI GMP Guidelines", "Section 3.2 — Lighting", 2),
        ("GMP_PREM_VENT", "Premises & Facilities", "Ventilation and air quality control", "Effective ventilation must prevent condensation, remove cooking odours and vapours, and prevent air-borne contamination of food. Air flow must not move from contaminated to clean areas.", 5.0, True, "SLSI GMP Guidelines", "Section 3.3 — Ventilation", 3),
        ("GMP_PREM_SANIT", "Premises & Facilities", "Dedicated sanitary facilities for staff", "Clean toilet facilities separate from production areas must be available for all staff. Handwashing signs must be posted. Facilities must not open directly to food handling areas.", 4.0, True, "SLSI GMP Guidelines", "Section 3.4 — Sanitary Facilities", 4),
        ("GMP_PERS_HEALTH", "Personnel Hygiene", "Food handler health screening policy", "Personnel showing symptoms of illness including diarrhoea, vomiting, skin lesions, or respiratory infection must be excluded from food contact areas. A health declaration procedure must be documented.", 6.0, True, "SLSI GMP Guidelines", "Section 4.1 — Health Screening", 5),
        ("GMP_PERS_DRESS", "Personnel Hygiene", "Protective clothing and PPE use", "All food handlers must wear clean protective clothing (overalls/aprons), head covering, and appropriate footwear. Jewellery, watches, and mobile phones must not be worn in production areas.", 5.0, False, "SLSI GMP Guidelines", "Section 4.2 — Protective Clothing", 6),
        ("GMP_PERS_WASH", "Personnel Hygiene", "Handwashing compliance and training", "Staff must wash hands at defined checkpoints: entry to production area, after toilet use, after handling raw materials, and after any contamination risk. Training records must be maintained.", 4.0, True, "SLSI GMP Guidelines", "Section 4.3 — Handwashing Procedures", 7),
        ("GMP_EQUIP_DESIGN", "Equipment & Maintenance", "Food-grade, cleanable equipment surfaces", "All equipment in contact with food must be made of food-grade, non-toxic, non-corrosive materials. Surfaces must be smooth, non-porous, and designed for easy cleaning and inspection.", 6.0, True, "SLSI GMP Guidelines", "Section 5.1 — Equipment Design", 8),
        ("GMP_EQUIP_MAINT", "Equipment & Maintenance", "Preventive maintenance programme", "A documented preventive maintenance schedule must be maintained. Maintenance activities must be recorded. Equipment must be re-cleaned and sanitised after maintenance before food production resumes.", 5.0, False, "SLSI GMP Guidelines", "Section 5.2 — Preventive Maintenance", 9),
        ("GMP_EQUIP_CALIB", "Equipment & Maintenance", "Calibration of measuring and monitoring equipment", "Thermometers, scales, pH meters, and other critical measuring instruments must be calibrated at defined intervals. Calibration records must be retained.", 4.0, False, "SLSI GMP Guidelines", "Section 5.3 — Calibration", 10),
        ("GMP_WATER_POTABLE", "Water & Utilities", "Safe and potable water supply", "Water used in food production, cleaning, and as an ingredient must meet Sri Lanka potable water standards. Non-potable water systems must be clearly identified and physically separated.", 7.0, True, "SLSI GMP Guidelines", "Section 6.1 — Water Supply", 11),
        ("GMP_WATER_TEST", "Water & Utilities", "Periodic water quality testing", "Potable water used in food production must be tested microbiologically and chemically at least annually by an accredited laboratory. Test records must be retained.", 3.0, False, "SLSI GMP Guidelines", "Section 6.2 — Water Testing", 12),
        ("GMP_PROD_CTRL", "Production Controls", "Defined processing steps and parameters", "All production steps must be documented with defined parameters (time, temperature, speed, concentration). Deviations must be recorded and assessed before product release.", 6.0, False, "SLSI GMP Guidelines", "Section 7.1 — Process Control", 13),
        ("GMP_PROD_REWORK", "Production Controls", "Rework and non-conforming product control", "Non-conforming products must be clearly identified and segregated. A documented procedure for rework, rejection, or disposal must be followed and recorded.", 4.0, False, "SLSI GMP Guidelines", "Section 7.3 — Non-Conforming Product", 14),
        ("GMP_PROD_ALLERGEN", "Production Controls", "Allergen management", "If allergens are present in the facility, procedures must prevent cross-contact. Allergens must be declared on labels in accordance with the Food Act regulations.", 5.0, True, "SLSI GMP Guidelines", "Section 7.4 — Allergen Control", 15),
        ("GMP_PEST_PROGRAMME", "Pest & Waste Control", "Documented pest control programme", "A licensed pest control contractor must inspect at defined intervals. Maps of bait stations and traps must be maintained. Evidence of pest activity must trigger documented corrective action.", 5.0, True, "SLSI GMP Guidelines", "Section 8.1 — Pest Control", 16),
        ("GMP_WASTE_MGMT", "Pest & Waste Control", "Waste management and removal", "Food and non-food waste must be collected in covered, identified containers and removed from production areas frequently. Waste storage areas must not attract pests.", 5.0, False, "SLSI GMP Guidelines", "Section 8.2 — Waste Management", 17),
        ("GMP_DOC_RECORDS", "Documentation & Records", "Mandatory GMP record set", "The following records must be maintained: cleaning logs, pest control records, staff training records, maintenance logs, calibration records, and non-conformance reports. Minimum retention: 2 years.", 5.0, False, "SLSI GMP Guidelines", "Section 9.1 — Record Keeping", 18),
    ]

    for rid, cat_lbl, title, desc, w, safety, sdoc, sclause, dorder in gmp_reqs:
        db.merge(SchemeRequirement(
            id=rid, scheme_id="SLS_GMP", category_label=cat_lbl, title=title,
            description=desc, weight=Decimal(str(w)), safety_critical=safety,
            source_document=sdoc, clause_reference=sclause, source_url="",
            content_verified=False, evaluation_rule={}, display_order=dorder, active=True,
        ))

    gmp_costs = [
        (
            "COST_GMP_SLSI_FEE",
            "GMP_SLSI_APPLICATION",
            "SLSI GMP Certification fee",
            CostType.CERTIFYING_BODY_FEE,
            40000,
            120000,
            20000,
            60000,
            "SLSI GMP fee schedule (estimate). Varies by production scale.",
        ),
        (
            "COST_GMP_GAP",
            "GMP_GAP_ASSESSMENT",
            "GMP gap assessment by consultant",
            CostType.BUSINESS_CAPEX,
            30000,
            75000,
            0,
            0,
            "One-off engagement with food safety consultant to identify gaps.",
        ),
        (
            "COST_GMP_DOC_SETUP",
            "GMP_DOC_SETUP",
            "GMP documentation system setup",
            CostType.BUSINESS_CAPEX,
            5000,
            20000,
            0,
            2000,
            "Templates, record books, and labelling for GMP records.",
        ),
        (
            "COST_GMP_TRAINING",
            "GMP_TRAINING",
            "GMP staff training programme",
            CostType.BUSINESS_CAPEX,
            15000,
            50000,
            5000,
            20000,
            "On-site training sessions for production staff on GMP requirements.",
        ),
        (
            "COST_GMP_AUDIT",
            "GMP_AUDIT",
            "SLSI annual GMP surveillance audit",
            CostType.CERTIFYING_BODY_FEE,
            0,
            0,
            20000,
            60000,
            "Annual SLSI audit fee to maintain GMP certification.",
        ),
    ]

    for cid, aref, title, ctype, ot_min, ot_max, rec_min, rec_max, note in gmp_costs:
        db.merge(
            SchemeCostItem(
                id=cid,
                scheme_id="SLS_GMP",
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

    # ── HACCP Certification ───────────────────────────────────────────────────
    haccp_weights = {
        "HACCP Foundations": 15,
        "Hazard Analysis": 20,
        "Critical Control Points": 25,
        "Monitoring & Corrective Action": 20,
        "Verification & Validation": 10,
        "Documentation & Records": 10,
    }
    db.merge(
        CertificationScheme(
            id="SLS_HACCP",
            name="HACCP Certification",
            short_code="HACCP",
            track=CertificationTrack.PROCESS_MANAGEMENT,
            body_id="SLSI",
            product_id=None,
            mandatory_tier=MandatoryTier.MARKET_REQUIRED,
            applicability_rule={
                "market": ["supermarket", "institutional", "export"],
                "mandatory_note": "Required by all major Sri Lankan supermarket chains, government institutional food contracts, and most export markets. Prerequisite for ISO 22000."
            },
            category_weights=haccp_weights,
            summary="HACCP (Hazard Analysis and Critical Control Points) certification issued by SLSI. A science-based systematic approach to identifying and controlling food safety hazards. Required by supermarkets, hotels, and all export markets.",
            typical_timeline_days=270,
            source_url="https://www.slsi.lk/haccp.html",
            active=True,
            display_order=2,
        )
    )
    db.flush()  # ensure scheme row is written before FK-dependent children

    haccp_reqs = [
        ("HACCP_TEAM", "HACCP Foundations", "Designated HACCP team with defined roles", "A multi-disciplinary HACCP team must be appointed. At least one member must have formal HACCP training. Roles and responsibilities must be documented.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969 / SLSI HACCP Guidelines", "Principle 0 — HACCP Team", 1),
        ("HACCP_SCOPE", "HACCP Foundations", "Defined product description and intended use", "A written description of each product including composition, physicochemical properties, packaging, shelf life, and intended consumer must be documented before hazard analysis.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969", "Step 2 — Product Description", 2),
        ("HACCP_FLOW", "HACCP Foundations", "Verified process flow diagram", "A process flow diagram must be drawn for every product covered by the HACCP plan. The diagram must be verified on-site to confirm it accurately reflects actual production.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969", "Steps 4–5 — Process Flow Diagram", 3),
        ("HACCP_HAZ_BIO", "Hazard Analysis", "Biological hazard identification for each process step", "For each step in the process flow, biological hazards (pathogens, spoilage organisms) must be systematically identified and their likelihood and severity assessed.", 7.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 1", "Step 6 — Biological Hazard Analysis", 4),
        ("HACCP_HAZ_CHEM", "Hazard Analysis", "Chemical hazard identification and assessment", "Chemical hazards (pesticide residues, cleaning chemical contamination, natural toxins, allergens) must be identified at each step and assessed for significance.", 7.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 1", "Step 6 — Chemical Hazard Analysis", 5),
        ("HACCP_HAZ_PHYS", "Hazard Analysis", "Physical hazard identification and assessment", "Physical hazards (glass, metal, bone, plastic) must be identified at each step and assessed for likelihood and severity. Detection controls must be specified.", 6.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 1", "Step 6 — Physical Hazard Analysis", 6),
        ("HACCP_CCP_IDENT", "Critical Control Points", "CCP identification using decision tree", "Critical Control Points (CCPs) must be identified for significant hazards using a systematic decision tree or equivalent method. The rationale for CCP determination must be documented.", 8.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 2", "Step 7 — CCP Determination", 7),
        ("HACCP_CL_DEFINED", "Critical Control Points", "Critical limits established for each CCP", "Validated critical limits (e.g. minimum cooking temperature, maximum pH, minimum Brix) must be established for every CCP. Limits must be based on scientific evidence or regulatory requirement.", 9.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 3", "Step 8 — Critical Limits", 8),
        ("HACCP_CL_VALIDATED", "Critical Control Points", "Critical limits scientifically validated", "Each critical limit must have documented scientific justification or reference to a recognised authority (e.g. SLSI, FSAI, Codex). Validation records must be retained.", 8.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 3", "Step 8 — CL Validation", 9),
        ("HACCP_MON_PROCEDURE", "Monitoring & Corrective Action", "Defined monitoring procedures for each CCP", "For each CCP, a defined monitoring procedure must specify: what is measured, how it is measured, frequency, and the responsible person. Monitoring must be able to detect loss of control in time.", 8.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 4", "Step 9 — Monitoring System", 10),
        ("HACCP_MON_RECORDS", "Monitoring & Corrective Action", "CCP monitoring records completed at time of operation", "Monitoring records must be completed by the responsible person at the time of observation. Records must include the actual measured value, not just pass/fail. Signature and date required.", 7.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 4", "Step 9 — Monitoring Records", 11),
        ("HACCP_CA_PROCEDURE", "Monitoring & Corrective Action", "Documented corrective action procedure", "A documented corrective action procedure must be in place for each CCP. It must specify: who is responsible, what happens to affected product, and how the root cause is addressed.", 7.0, True, "Codex Alimentarius CAC/RCP 1-1969 — Principle 5", "Step 10 — Corrective Actions", 12),
        ("HACCP_CA_RECORDS", "Monitoring & Corrective Action", "Corrective action events recorded", "Every corrective action triggered by a CCP deviation must be documented, including the nature of the deviation, disposition of the affected product, and preventive measure implemented.", 6.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 5", "Step 10 — Corrective Action Records", 13),
        ("HACCP_VERIF_INTERNAL", "Verification & Validation", "Internal verification audit schedule", "Periodic internal verification activities (e.g. internal audits, CCP record review, equipment calibration checks) must be scheduled and carried out at least annually. Findings must be documented.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 6", "Step 11 — Verification", 14),
        ("HACCP_VERIF_LAB", "Verification & Validation", "End-product or environmental microbiological testing", "Microbiological testing of finished product or processing environment must be conducted periodically to verify the effectiveness of the HACCP plan.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 6", "Step 11 — Verification Testing", 15),
        ("HACCP_DOC_PLAN", "Documentation & Records", "Documented and approved HACCP plan", "A written HACCP plan covering all seven HACCP principles must be in place. The plan must be reviewed and approved by management and reviewed whenever there is any change to product, process, or ingredients.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 7", "Step 12 — HACCP Documentation", 16),
        ("HACCP_DOC_RETENTION", "Documentation & Records", "Record retention and security", "HACCP monitoring records, corrective action records, verification records, and the HACCP plan must be retained for a minimum period sufficient to cover the product shelf life plus one year, or as required by regulation.", 3.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 7", "Step 12 — Record Retention", 17),
        ("HACCP_TRAINING", "HACCP Foundations", "HACCP team and operator training", "All HACCP team members must receive formal HACCP training. Production operators working at CCPs must receive role-specific training. Training records must document the content, date, trainer, and attendees.", 5.0, False, "SLSI HACCP Guidelines", "Section 2.3 — Training Requirements", 18),
        ("HACCP_PREREQ", "HACCP Foundations", "Documented prerequisite programmes (PRPs)", "Prerequisite programmes including GMP, pest control, cleaning and sanitation, water control, and allergen management must be documented and maintained as the foundation of the HACCP system.", 5.0, False, "Codex Alimentarius CAC/RCP 1-1969", "Step 1 — Prerequisite Programmes", 19),
        ("HACCP_REVIEW", "Documentation & Records", "HACCP system review after significant change", "The HACCP plan must be formally reviewed whenever there is a change in raw materials, product formulation, processing methods, equipment, packaging, intended use, or a food safety incident.", 2.0, False, "Codex Alimentarius CAC/RCP 1-1969 — Principle 7", "Step 12 — System Review", 20),
    ]

    for rid, cat_lbl, title, desc, w, safety, sdoc, sclause, dorder in haccp_reqs:
        db.merge(SchemeRequirement(
            id=rid, scheme_id="SLS_HACCP", category_label=cat_lbl, title=title,
            description=desc, weight=Decimal(str(w)), safety_critical=safety,
            source_document=sdoc, clause_reference=sclause, source_url="",
            content_verified=False, evaluation_rule={}, display_order=dorder, active=True,
        ))

    haccp_costs = [
        (
            "COST_HACCP_SLSI_FEE",
            "HACCP_CERTIFICATION",
            "SLSI HACCP Certification fee",
            CostType.CERTIFYING_BODY_FEE,
            60000,
            180000,
            30000,
            90000,
            "SLSI HACCP certification fee (estimate). Varies by product range and scale.",
        ),
        (
            "COST_HACCP_CONSULTANT",
            "HACCP_CONSULTANT",
            "HACCP plan development by consultant",
            CostType.BUSINESS_CAPEX,
            75000,
            200000,
            0,
            0,
            "Qualified food safety consultant to develop the full HACCP plan including hazard analysis and CCP studies.",
        ),
        (
            "COST_HACCP_TRAINING",
            "HACCP_TRAINING",
            "HACCP Level 2 training for team",
            CostType.BUSINESS_CAPEX,
            25000,
            75000,
            10000,
            30000,
            "Recognised HACCP training programme (e.g. SLSI, SRI, or equivalent). Include annual refresher.",
        ),
        (
            "COST_HACCP_LAB",
            "HACCP_LAB_TESTING",
            "Product and environmental microbiological testing",
            CostType.LAB_TESTING_FEE,
            50000,
            150000,
            25000,
            75000,
            "Baseline and periodic microbiological verification testing at SLSI-accredited laboratory.",
        ),
        (
            "COST_HACCP_EQUIP",
            "HACCP_MONITORING_EQUIP",
            "CCP monitoring equipment (calibrated thermometers, pH meters)",
            CostType.BUSINESS_CAPEX,
            20000,
            60000,
            5000,
            15000,
            "Food-grade, calibrated monitoring instruments for each CCP.",
        ),
        (
            "COST_HACCP_AUDIT",
            "HACCP_AUDIT",
            "Annual SLSI HACCP surveillance audit",
            CostType.CERTIFYING_BODY_FEE,
            0,
            0,
            30000,
            90000,
            "Annual SLSI audit required to maintain HACCP certification status.",
        ),
    ]

    for cid, aref, title, ctype, ot_min, ot_max, rec_min, rec_max, note in haccp_costs:
        db.merge(
            SchemeCostItem(
                id=cid,
                scheme_id="SLS_HACCP",
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

    # ── ISO 22000:2018 Food Safety Management ─────────────────────────────────
    iso_weights = {
        "Organizational Context": 5,
        "Leadership & Commitment": 10,
        "Planning": 10,
        "Prerequisite Programmes": 15,
        "HACCP Plan": 20,
        "Operational Controls": 15,
        "Performance Evaluation": 15,
        "Improvement": 10,
    }
    # Re-merge ISO 22000 as active now Phase 2 is authorized
    db.merge(
        CertificationScheme(
            id="ISO_22000",
            name="ISO 22000:2018 Food Safety Management",
            short_code="ISO_22000",
            track=CertificationTrack.PROCESS_MANAGEMENT,
            body_id="ISO",
            product_id=None,
            mandatory_tier=MandatoryTier.OPTIONAL,
            applicability_rule={
                "market": ["export"],
                "note": "Strongly recommended for export to regulated markets (EU, US, AU, Middle East). Internationally recognised FSMS standard. Builds on HACCP and GMP."
            },
            category_weights=iso_weights,
            summary="ISO 22000:2018 specifies requirements for a Food Safety Management System (FSMS). It integrates GMP, HACCP, and management system requirements. Required or strongly preferred by most regulated export markets and global retail buyers.",
            typical_timeline_days=540,
            source_url="https://www.iso.org/iso-22000-food-safety-management.html",
            active=True,
            display_order=3,
        )
    )
    db.flush()  # ensure scheme row is written before FK-dependent children

    iso_reqs = [
        ("ISO_CTX_SCOPE", "Organizational Context", "Defined FSMS scope and organizational context", "The scope of the Food Safety Management System must be defined, including the products, processes, and sites covered. Internal and external factors relevant to food safety must be identified (ISO 22000 Clause 4.1–4.3).", 5.0, False, "ISO 22000:2018", "Clause 4.1–4.3 — Context and Scope", 1),
        ("ISO_CTX_INTERESTED", "Organizational Context", "Interested party needs and regulatory requirements identified", "The needs and expectations of interested parties (customers, regulators, consumers) relevant to food safety must be identified and considered in the FSMS design.", 5.0, False, "ISO 22000:2018", "Clause 4.2 — Interested Parties", 2),
        ("ISO_LEAD_POLICY", "Leadership & Commitment", "Food safety policy established and communicated", "Top management must establish a food safety policy appropriate to the organization's purpose. The policy must be documented, communicated to all staff, and reviewed periodically.", 5.0, False, "ISO 22000:2018", "Clause 5.2 — Food Safety Policy", 3),
        ("ISO_LEAD_ROLES", "Leadership & Commitment", "FSMS roles and responsibilities defined", "Top management must appoint a Food Safety Team Leader and define FSMS roles and responsibilities. Authority must be documented to enable the FSMS to function effectively.", 5.0, False, "ISO 22000:2018", "Clause 5.3 — Roles and Responsibilities", 4),
        ("ISO_PLAN_OBJECTIVES", "Planning", "Measurable food safety objectives established", "Food safety objectives must be set, measurable, consistent with the policy, and reviewed. Plans to achieve objectives must include resources, responsible persons, timelines, and evaluation methods.", 5.0, False, "ISO 22000:2018", "Clause 6.2 — Food Safety Objectives", 5),
        ("ISO_PLAN_RISK", "Planning", "Risk and opportunity assessment for FSMS", "Risks and opportunities relevant to the FSMS must be determined and addressed through planning actions. This includes both positive opportunities (e.g. technology improvements) and negative risks (e.g. supply chain disruption).", 5.0, False, "ISO 22000:2018", "Clause 6.1 — Risks and Opportunities", 6),
        ("ISO_PRP_INFRA", "Prerequisite Programmes", "Infrastructure PRPs — premises, equipment, and utilities", "PRPs addressing infrastructure (building, equipment, utilities including water, energy, and ventilation) must be documented, implemented, and monitored to prevent food safety hazards.", 6.0, True, "ISO 22000:2018", "Clause 8.2 — Prerequisite Programmes", 7),
        ("ISO_PRP_CLEAN", "Prerequisite Programmes", "Cleaning and disinfection PRP", "A documented cleaning and disinfection PRP must define schedules, methods, materials, and verification. Records must confirm completion.", 5.0, True, "ISO 22000:2018", "Clause 8.2 — Cleaning & Disinfection PRP", 8),
        ("ISO_PRP_ALLERGEN", "Prerequisite Programmes", "Allergen management PRP", "An allergen management PRP must identify allergens present and specify procedures to prevent cross-contact. Allergen declarations on labels must be controlled.", 5.0, True, "ISO 22000:2018", "Clause 8.2 — Allergen PRP", 9),
        ("ISO_PRP_PERSONNEL", "Prerequisite Programmes", "Personnel hygiene and training PRP", "A documented personnel hygiene PRP must specify requirements for health screening, protective clothing, handwashing, and training. Records of training completion must be maintained.", 4.0, False, "ISO 22000:2018", "Clause 8.2 — Personnel Hygiene PRP", 10),
        ("ISO_HACCP_ANALYSIS", "HACCP Plan", "FSMS HACCP hazard analysis completed", "A complete hazard analysis must identify biological, chemical, and physical hazards at each process step. Risk assessment must determine which hazards are significant and require OPRP or CCP control.", 8.0, True, "ISO 22000:2018", "Clause 8.5.2 — Hazard Analysis", 11),
        ("ISO_HACCP_CCPS", "HACCP Plan", "CCPs and OPRPs defined with critical limits", "Critical Control Points (CCPs) and Operational PRPs (OPRPs) must be established for all significant hazards. Critical limits must be defined and scientifically validated.", 9.0, True, "ISO 22000:2018", "Clause 8.5.4–8.5.7 — CCPs and OPRPs", 12),
        ("ISO_HACCP_MONITOR", "HACCP Plan", "CCP and OPRP monitoring system in operation", "A monitoring system for each CCP and OPRP must be implemented and records maintained. The monitoring frequency must be sufficient to ensure control is maintained.", 8.0, True, "ISO 22000:2018", "Clause 8.5.4.3 — Monitoring", 13),
        ("ISO_OPS_TRACEABILITY", "Operational Controls", "Traceability system for all food materials", "A traceability system must enable identification of material lots, processing records, and distribution destinations. Product recall must be achievable within 24 hours.", 6.0, False, "ISO 22000:2018", "Clause 8.3 — Traceability System", 14),
        ("ISO_OPS_EMERGENCY", "Operational Controls", "Emergency preparedness and crisis management", "Procedures must be in place to respond to potential emergency situations or accidents affecting food safety. Crisis management roles and communication plans must be documented.", 4.0, False, "ISO 22000:2018", "Clause 8.4.2 — Emergency Preparedness", 15),
        ("ISO_OPS_WITHDRAWAL", "Operational Controls", "Product withdrawal and recall procedure", "A documented withdrawal/recall procedure must be in place, tested at defined intervals, and ensure affected product can be identified and removed from the market rapidly.", 5.0, True, "ISO 22000:2018", "Clause 8.9.5 — Product Recall", 16),
        ("ISO_EVAL_INTERNAL", "Performance Evaluation", "Planned internal audit programme", "An internal audit programme covering all elements of the FSMS must be conducted at planned intervals. Auditors must not audit their own work. Findings and corrective actions must be recorded.", 5.0, False, "ISO 22000:2018", "Clause 9.2 — Internal Audit", 17),
        ("ISO_EVAL_MANAGEMENT", "Performance Evaluation", "Management review at planned intervals", "Top management must review the FSMS at planned intervals to ensure its continued suitability, adequacy, and effectiveness. Management review outputs must include decisions on FSMS improvement.", 5.0, False, "ISO 22000:2018", "Clause 9.3 — Management Review", 18),
        ("ISO_EVAL_KPI", "Performance Evaluation", "Key performance indicators for food safety objectives", "Measurable food safety KPIs must be monitored and reported in management reviews to demonstrate progress towards food safety objectives.", 5.0, False, "ISO 22000:2018", "Clause 9.1 — Monitoring and Measurement", 19),
        ("ISO_IMPROVE_NC", "Improvement", "Nonconformity and corrective action process", "A documented nonconformity management process must ensure root cause analysis and corrective action for all significant FSMS failures. Effectiveness of corrective actions must be verified.", 5.0, False, "ISO 22000:2018", "Clause 10.1 — Nonconformity and Corrective Action", 20),
        ("ISO_IMPROVE_UPDATE", "Improvement", "Continual improvement of the FSMS", "The organisation must continually improve the suitability and effectiveness of the FSMS. Actions taken for improvement must be reviewed for effectiveness in the next management review.", 5.0, False, "ISO 22000:2018", "Clause 10.3 — Continual Improvement", 21),
        ("ISO_IMPROVE_UPDATE_FSMS", "Improvement", "FSMS updated following system changes", "The FSMS documentation and HACCP plan must be updated whenever there is a change in products, processes, ingredients, technology, regulatory requirements, or food safety incidents.", 5.0, False, "ISO 22000:2018", "Clause 10.3 — FSMS Update", 22),
    ]

    for rid, cat_lbl, title, desc, w, safety, sdoc, sclause, dorder in iso_reqs:
        db.merge(SchemeRequirement(
            id=rid, scheme_id="ISO_22000", category_label=cat_lbl, title=title,
            description=desc, weight=Decimal(str(w)), safety_critical=safety,
            source_document=sdoc, clause_reference=sclause, source_url="",
            content_verified=False, evaluation_rule={}, display_order=dorder, active=True,
        ))

    iso_costs = [
        (
            "COST_ISO_CB_INITIAL",
            "ISO_CERTIFICATION_INITIAL",
            "IAF-accredited certification body — initial certification audit",
            CostType.CERTIFYING_BODY_FEE,
            200000,
            500000,
            0,
            0,
            "Stage 1 (document review) + Stage 2 (site audit) by an accredited CB. Fee varies by CB and company size.",
        ),
        (
            "COST_ISO_GAP",
            "ISO_GAP_ASSESSMENT",
            "ISO 22000 gap assessment",
            CostType.BUSINESS_CAPEX,
            75000,
            200000,
            0,
            0,
            "Initial gap analysis by qualified food safety consultant against ISO 22000:2018 requirements.",
        ),
        (
            "COST_ISO_FSMS_CONSULTANT",
            "ISO_FSMS_CONSULTANT",
            "FSMS implementation consultant",
            CostType.BUSINESS_CAPEX,
            150000,
            400000,
            0,
            0,
            "Consultant to develop FSMS documentation, hazard analysis, and HACCP plan aligned to ISO 22000.",
        ),
        (
            "COST_ISO_TRAINING",
            "ISO_TRAINING",
            "ISO 22000 Lead Implementer or Internal Auditor training",
            CostType.BUSINESS_CAPEX,
            50000,
            150000,
            15000,
            40000,
            "Formal training for FSMS team leader and internal auditors. Include periodic refresher.",
        ),
        (
            "COST_ISO_LAB",
            "ISO_LAB_TESTING",
            "Product and process verification laboratory testing",
            CostType.LAB_TESTING_FEE,
            75000,
            200000,
            40000,
            100000,
            "Annual product and environmental testing required for HACCP verification within ISO 22000.",
        ),
        (
            "COST_ISO_SURVEILLANCE",
            "ISO_SURVEILLANCE_AUDIT",
            "Annual ISO 22000 surveillance audit",
            CostType.CERTIFYING_BODY_FEE,
            0,
            0,
            100000,
            250000,
            "Annual surveillance audit by IAF-accredited CB to maintain ISO 22000 certification.",
        ),
        (
            "COST_ISO_RECERT",
            "ISO_RECERTIFICATION",
            "ISO 22000 recertification audit (3-year cycle)",
            CostType.CERTIFYING_BODY_FEE,
            0,
            0,
            50000,
            150000,
            "Full recertification audit every 3 years. Amortised as annual recurring cost.",
        ),
    ]

    for cid, aref, title, ctype, ot_min, ot_max, rec_min, rec_max, note in iso_costs:
        db.merge(
            SchemeCostItem(
                id=cid,
                scheme_id="ISO_22000",
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
