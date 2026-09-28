from fastapi import APIRouter, HTTPException
from app.services.curriculum import (
    get_all_paths, get_path, get_module, get_lesson, CURRICULUM
)
from app.services.curriculum_meta import (
    CERT_REQUIREMENTS, MODULE_META, MODULE_LESSON_TOTALS, MODULE_ORDER, MODULE_PREREQS
)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


@router.get("/paths")
async def list_paths():
    return get_all_paths()


@router.get("/paths/{path_id}")
async def get_path_detail(path_id: str):
    path = get_path(path_id)
    if not path:
        raise HTTPException(404, "Path not found")
    return {
        **{k: v for k, v in path.items() if k != "modules"},
        "modules": [
            {
                **{k: v for k, v in m.items() if k != "lessons"},
                # lesson_count = content lessons only (excludes quiz lessons)
                "lesson_count": sum(1 for l in m["lessons"] if not l.get("is_quiz")),
                "lessons": [
                    {k: v for k, v in l.items() if k != "content"}
                    for l in m["lessons"]
                ],
            }
            for m in path["modules"]
        ],
    }


@router.get("/paths/{path_id}/modules/{module_id}")
async def get_module_detail(path_id: str, module_id: str):
    module = get_module(path_id, module_id)
    if not module:
        raise HTTPException(404, "Module not found")
    return {
        **{k: v for k, v in module.items() if k != "lessons"},
        "lessons": [
            {k: v for k, v in l.items() if k != "content"}
            for l in module["lessons"]
        ],
    }


@router.get("/paths/{path_id}/modules/{module_id}/lessons/{lesson_id}")
async def get_lesson_detail(path_id: str, module_id: str, lesson_id: str):
    lesson = get_lesson(path_id, module_id, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return lesson


@router.get("/meta")
async def get_curriculum_meta():
    """
    Serve structural curriculum facts for the frontend.
    Replaces all hardcoded MODULE_LESSON_TOTALS in frontend code.
    """
    return {
        "module_lesson_totals": MODULE_LESSON_TOTALS,
        "module_order":         MODULE_ORDER,
        "module_meta": {
            mid: {
                "path_id":            m["path_id"],
                "title":              m["title"],
                "lesson_ids":         m["lesson_ids"],
                "codercise_ids":      m["codercise_ids"],
                "quiz_id":            m["quiz_id"],
                "prereq_module_ids":  m.get("prereq_module_ids", []),
            }
            for mid, m in MODULE_META.items()
        },
        "cert_requirements": {
            pid: {
                "path_title":          r["path_title"],
                "required_lessons":    r["required_lessons"],
                "required_codercises": r["required_codercises"],
                "required_quizzes":    r["required_quizzes"],
                "passing_quiz_score":  r["passing_quiz_score"],
                "total_quizzes":       r["total_quizzes"],
                "quiz_ids":            r["quiz_ids"],
            }
            for pid, r in CERT_REQUIREMENTS.items()
        },
    }


@router.get("/map")
async def get_map_data():
    """Return node/edge data for the Codebook Map canvas."""
    nodes = []
    edges = []
    for path in CURRICULUM:
        for module in path["modules"]:
            # Count only content lessons for the node display
            content_lessons = sum(1 for l in module["lessons"] if not l.get("is_quiz"))
            nodes.append({
                "id":           module["id"],
                "path_id":      path["id"],
                "label":        module["abbreviation"],
                "title":        module["title"],
                "lesson_count": content_lessons,
                "completed":    0,
                "color":        path["color"],
            })
        mods = path["modules"]
        for i in range(len(mods) - 1):
            edges.append({"source": mods[i]["id"], "target": mods[i + 1]["id"]})

    return {"nodes": nodes, "edges": edges, "paths": get_all_paths()}
