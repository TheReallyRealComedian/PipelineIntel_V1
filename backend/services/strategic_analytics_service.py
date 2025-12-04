# backend/services/strategic_analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import db
from datetime import datetime

def get_manufacturing_challenges_forecast(db_session: Session, years_ahead: int = 5):
    """
    Forecasts top manufacturing challenges based on the pipeline's modality mix 
    and their standard challenges over the next N years.
    
    This function will be fully implemented later. For now, it's a placeholder.
    """
    print(f"Executing strategic query: Manufacturing challenges forecast for the next {years_ahead} years.")
    return {}


def get_modality_complexity_ranking(db_session: Session, timeline_filter: int = None):
    """
    Ranks modalities by their manufacturing complexity, derived from the number and
    complexity of their required capabilities.

    This function will be fully implemented later. For now, it's a placeholder.
    It would leverage the 'product_complexity_summary' view.
    """
    print(f"Executing strategic query: Modality complexity ranking for timeline '{timeline_filter or 'all time'}'.")
    return []


def get_weighted_challenges_data():
    """
    Berechnet eine gewichtete Liste von Manufacturing Challenges.
    KORRIGIERTE VERSION: Verhindert Cross-Joins zwischen Modalitäten.
    """
    sql = text("""
    WITH RECURSIVE
    -- 1. HIERARCHIE AUFLÖSEN
    StageHierarchy AS (
        SELECT
            stage_id, stage_name, parent_stage_id,
            stage_name as root_stage_name
        FROM process_stages
        WHERE parent_stage_id IS NULL

        UNION ALL

        SELECT
            child.stage_id, child.stage_name, child.parent_stage_id,
            parent.root_stage_name
        FROM process_stages child
        JOIN StageHierarchy parent ON child.parent_stage_id = parent.stage_id
    ),

    -- 2. PRODUKT-TECHNOLOGIE (MIT FILTERUNG)
    -- Hier liegt der Fix: Wir filtern Technologien strikt nach Modalität/Template
    ProductTechnologies AS (
        -- A. Via Template-Logik (Der komplexe Teil)
        SELECT DISTINCT p.product_id, mt.technology_id
        FROM products p
        -- Link zum Template und den Stages
        JOIN template_stages ts ON p.process_template_id = ts.template_id
        -- Link zur Technologie via Stage
        JOIN manufacturing_technologies mt ON ts.stage_id = mt.stage_id

        WHERE p.process_template_id IS NOT NULL
        AND (
            -- FILTER 1: Technologie ist spezifisch für dieses Template
            mt.template_id = p.process_template_id

            OR

            -- FILTER 2: Technologie ist spezifisch für die Modalität des Produkts
            -- (Check in der Junction Table technology_modalities)
            mt.technology_id IN (
                SELECT tm.technology_id
                FROM technology_modalities tm
                WHERE tm.modality_id = p.modality_id
            )

            OR

            -- FILTER 3: Technologie ist generisch (Weder Template noch Modalität zugeordnet)
            (
                mt.template_id IS NULL
                AND NOT EXISTS (
                    SELECT 1 FROM technology_modalities tm
                    WHERE tm.technology_id = mt.technology_id
                )
            )
        )

        UNION

        -- B. Via direkter, manueller Verknüpfung am Produkt
        SELECT pt.product_id, pt.technology_id
        FROM product_to_technology pt
    ),

    -- 3. PRODUKT-CHALLENGES (Via Tech + Explizit)
    RawChallenges AS (
        -- A. Via Technology (die wir oben gefiltert haben)
        SELECT pt.product_id, mc.challenge_id
        FROM ProductTechnologies pt
        JOIN manufacturing_challenges mc ON pt.technology_id = mc.technology_id

        UNION

        -- B. Explizit am Produkt (Manuelle Overrides)
        SELECT pc.product_id, pc.challenge_id
        FROM product_to_challenge pc
        WHERE pc.relationship_type = 'explicit'
    ),

    -- 4. BEREINIGUNG (Exclusions entfernen)
    EffectiveChallenges AS (
        SELECT rc.product_id, rc.challenge_id
        FROM RawChallenges rc
        WHERE NOT EXISTS (
            SELECT 1 FROM product_to_challenge exc
            WHERE exc.product_id = rc.product_id
            AND exc.challenge_id = rc.challenge_id
            AND exc.relationship_type = 'excluded'
        )
    )

    -- 5. FINALE AGGREGATION
    SELECT
        mc.challenge_name,
        mc.severity_level,
        mt.technology_name,
        COALESCE(sh.root_stage_name, 'General Process') as process_area,
        COUNT(DISTINCT ec.product_id) as frequency,
        MIN(p.expected_launch_year) as next_impact_year,
        string_agg(DISTINCT p.product_code, ', ') as affected_products_list
    FROM EffectiveChallenges ec
    JOIN manufacturing_challenges mc ON ec.challenge_id = mc.challenge_id
    JOIN products p ON ec.product_id = p.product_id
    LEFT JOIN manufacturing_technologies mt ON mc.technology_id = mt.technology_id
    LEFT JOIN StageHierarchy sh ON mt.stage_id = sh.stage_id

    -- Nur aktive Produkte
    WHERE (p.project_status IS NULL OR p.project_status != 'Discontinued')

    GROUP BY
        mc.challenge_id, mc.challenge_name, mc.severity_level,
        mt.technology_name, sh.root_stage_name

    ORDER BY
        frequency DESC,
        next_impact_year ASC NULLS LAST
    """)

    result = db.session.execute(sql)

    data = []
    current_year = datetime.now().year

    for row in result:
        row_dict = dict(row._mapping)
        impact_year = row_dict.get('next_impact_year')

        if impact_year:
            row_dict['years_until'] = impact_year - current_year
        else:
            row_dict['years_until'] = 99

        data.append(row_dict)

    return data