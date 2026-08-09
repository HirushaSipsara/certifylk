"""Connect SLS cordial requirements to existing deterministic rules.

Revision ID: 20260809_0010
Revises: 20260809_0009
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "20260809_0010"
down_revision = "20260809_0009"
branch_labels = None
depends_on = None


RULES: dict[str, dict[str, object]] = {
    "SLS_HYG_HANDWASH": {
        "question": "HYG_HAND_01",
        "confirmed": ["always"],
        "partial": ["sometimes"],
        "gap": ["never"],
    },
    "SLS_HYG_CLEANING": {
        "question": "HYG_CLEAN_01",
        "confirmed": ["recorded_each_batch"],
        "partial": ["routine_no_record"],
        "gap": ["only_when_dirty"],
    },
    "SLS_HYG_CHEMICAL": {
        "question": "HYG_CHEM_01",
        "confirmed": ["locked_separate"],
        "partial": ["separate_area"],
        "gap": ["with_ingredients"],
    },
    "SLS_HYG_PEST": {
        "question": "HYG_PEST_01",
        "confirmed": ["logged"],
        "partial": ["checked_not_logged"],
        "gap": ["not_checked"],
    },
    "SLS_PROC_STAGES": {"derived": "process_steps"},
    "SLS_PROC_TEMP": {
        "question": "PROC_TEMP_01",
        "confirmed": ["thermometer"],
        "partial": ["time_and_appearance"],
        "gap": ["appearance_only"],
    },
    "SLS_PROC_FILL": {
        "question": "PACK_FILL_01",
        "confirmed": ["dedicated_clean_area"],
        "partial": ["cleaned_shared_area"],
        "gap": ["uncontrolled_area"],
    },
    "SLS_PROC_SEP": {
        "question": "PROC_SEP_01",
        "confirmed": ["separate_time_area"],
        "partial": ["clean_between"],
        "gap": ["same_without_cleaning"],
    },
    "SLS_DOC_BATCH": {
        "question": "DOC_BATCH_01",
        "confirmed": ["always"],
        "partial": ["sometimes"],
        "gap": ["never"],
    },
    "SLS_DOC_CLEANING": {
        "question": "DOC_CLEAN_01",
        "confirmed": ["every_day"],
        "partial": ["sometimes"],
        "gap": ["never"],
    },
    "SLS_SUP_SOURCE": {
        "question": "SUP_SOURCE_01",
        "confirmed": ["approved_regular"],
        "partial": ["known_variable"],
        "gap": ["unknown_cash"],
    },
    "SLS_SUP_REGISTER": {
        "question": "SUP_REG_01",
        "confirmed": ["complete"],
        "partial": ["informal"],
        "gap": ["none"],
    },
    "SLS_SUP_INCOMING": {
        "question": "SUP_CHECK_01",
        "confirmed": ["check_record"],
        "partial": ["check_no_record"],
        "gap": ["no_check"],
    },
    "SLS_PACK_LABEL": {
        "question": "PACK_LABEL_01",
        "confirmed": ["complete"],
        "partial": ["some_details"],
        "gap": ["name_only"],
    },
    "SLS_PACK_FOODGRADE": {
        "question": "PACK_GRADE_01",
        "confirmed": ["documented"],
        "partial": ["supplier_statement"],
        "gap": ["none"],
    },
    "SLS_STORE_INGREDIENT": {
        "question": "STORE_RAISED_01",
        "confirmed": ["raised_closed"],
        "partial": ["raised_open"],
        "gap": ["on_floor"],
    },
    "SLS_STORE_FINISHED": {
        "question": "STORE_FIN_01",
        "confirmed": ["separate_protected"],
        "partial": ["shared_protected"],
        "gap": ["unprotected"],
    },
    "SLS_TRACE_BATCH": {
        "question": "TRACE_CODE_01",
        "confirmed": ["every_batch"],
        "partial": ["date_only"],
        "gap": ["none"],
    },
    "SLS_TRACE_DIST": {
        "question": "TRACE_SALES_01",
        "confirmed": ["batch_customer"],
        "partial": ["sales_only"],
        "gap": ["none"],
    },
}


def upgrade() -> None:
    connection = op.get_bind()
    statement = sa.text(
        "UPDATE scheme_requirements SET evaluation_rule = CAST(:rule AS jsonb) "
        "WHERE id = :requirement_id AND scheme_id = 'SLS_MARK_CORDIAL'"
    )
    for requirement_id, rule in RULES.items():
        connection.execute(
            statement,
            {"requirement_id": requirement_id, "rule": json.dumps(rule)},
        )


def downgrade() -> None:
    connection = op.get_bind()
    statement = sa.text(
        "UPDATE scheme_requirements SET evaluation_rule = CAST('{}' AS jsonb) "
        "WHERE id = :requirement_id AND scheme_id = 'SLS_MARK_CORDIAL'"
    )
    for requirement_id in RULES:
        connection.execute(statement, {"requirement_id": requirement_id})
