"""Flask web application for JiuZhang with full i18n support."""

import os
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS

from jiuzhang.core.config import Config
from jiuzhang.core.multi_provider_api import MultiProviderClient
from jiuzhang.math_engine.lesson import LessonGenerator
from jiuzhang.math_engine.visualizer import Visualizer
from jiuzhang.courses.registry import CourseRegistry
from jiuzhang.i18n import I18n, SUPPORTED_LANGUAGES
from jiuzhang.research.engine import ResearchEngine
from jiuzhang.learning_tracker import LearningTracker
from jiuzhang.math_reasoning import MathReasoningEngine


def _validate_input(data, schema):
    """Validate input data against a schema."""
    validated = {}
    for field, (validator, required, default) in schema.items():
        value = data.get(field, default)
        if required and value is None:
            return None, f"Missing required field: {field}"
        if value is not None:
            try:
                validated[field] = validator(value)
            except (ValueError, TypeError) as e:
                return None, f"Invalid {field}: {str(e)}"
        else:
            validated[field] = default
    return validated, None


def _safe_str(value):
    """Validate string input."""
    if not isinstance(value, str):
        raise ValueError("Must be string")
    if len(value) > 1000:
        raise ValueError("String too long")
    return value


def _safe_int_range(min_val=0, max_val=1000000):
    """Create validator for integer in range."""
    def validator(value):
        val = int(value)
        if val < min_val or val > max_val:
            raise ValueError(f"Value must be between {min_val} and {max_val}")
        return val
    return validator


def _validate_provider(provider):
    """Validate provider exists."""
    valid_providers = ["ollama", "openai", "anthropic", "gemini", "deepseek"]
    if provider not in valid_providers:
        raise ValueError(f"Invalid provider: {provider}")
    return provider


def _validate_language(lang):
    """Validate language code."""
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}")
    return lang


def _validate_depth(depth):
    """Validate depth parameter."""
    if depth not in ["basic", "medium", "deep"]:
        raise ValueError("depth must be basic, medium, or deep")
    return depth


def _safe_eval_function(func_str: str):
    """Safely evaluate a mathematical function string using SymPy.

    Uses SymPy's parsing but restricts to safe mathematical expressions
    by limiting the allowed operations and rejecting dangerous patterns.
    """
    import math
    import re
    from sympy import sympify, lambdify, symbols
    
    # First, do a simple regex check to reject obvious dangerous patterns
    dangerous_patterns = [
        r'__\w+__',           # Magic methods
        r'\.__\w+__',         # Attribute access to magic methods
        r'\[\s*\w+\s*\]',     # Array indexing that might access dangerous objects
        r'import\s+',         # Import statements
        r'exec\s*\(',         # exec calls
        r'eval\s*\(',         # eval calls
        r'getattr\s*\(',      # getattr calls
        r'hasattr\s*\(',      # hasattr calls
        r'globals\s*\(\)',    # globals() calls
        r'locals\s*\(\)',     # locals() calls
        r'__import__\s*\(',   # __import__ calls
        r'\.?\w+\s*\.\s*\w+', # Attribute access patterns
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, func_str, re.IGNORECASE):
            return None
    
    try:
        # Parse with SymPy but limit to basic mathematical operations
        expr = sympify(func_str, evaluate=False)
        
        # Convert to lambda function with safe modules
        x = symbols("x")
        return lambdify(x, expr, modules=["numpy", {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
            "exp": math.exp, "log": math.log, "log10": math.log10,
            "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil,
            "abs": abs, "pi": math.pi, "e": math.e,
            "pow": pow,
        }])
    except Exception:
        return None


def create_app(config: Config = None):
    """Create Flask application with i18n support."""
    app = Flask(__name__)

    secret_key = os.environ.get("JIUZHANG_SECRET")
    if not secret_key:
        raise RuntimeError(
            "JIUZHANG_SECRET environment variable is not set. "
            "Flask requires a secret key for session security. "
            "Set it with: export JIUZHANG_SECRET='your-secret-key'"
        )
    app.secret_key = secret_key
    # Enable CORS with configurable origins
    cors_origins = os.environ.get("JIUZHANG_CORS_ORIGINS", "*")
    if cors_origins == "*":
        CORS(app)
    else:
        # Parse comma-separated origins
        origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        CORS(app, origins=origins)

    cfg = config or Config()
    client = MultiProviderClient(cfg)
    lesson_gen = LessonGenerator(cfg)
    registry = CourseRegistry()
    curriculum = registry.build_curriculum()
    i18n = I18n(default_language=cfg.language)
    research_engine = ResearchEngine(cfg)
    math_reasoning = MathReasoningEngine(client, cfg)

    @app.before_request
    def set_language():
        lang = request.args.get("lang") or session.get("language") or cfg.language
        if lang in SUPPORTED_LANGUAGES:
            i18n.set_language(lang)
            session["language"] = lang

    @app.context_processor
    def inject_i18n():
        return {
            "t": i18n.t,
            "current_language": i18n.get_language(),
            "languages": SUPPORTED_LANGUAGES,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/learn", methods=["POST"])
    def api_learn():
        data = request.json
        topic = data.get("topic", "")
        level = data.get("level", "elementary")
        lang = data.get("language", i18n.get_language())
        result = lesson_gen.generate_lesson(topic, level=level, language=lang)
        if result.success:
            return jsonify({"success": True, "content": result.data})
        return jsonify({"success": False, "error": result.error}), 500

    @app.route("/api/exercise", methods=["POST"])
    def api_exercise():
        data = request.json
        topic = data.get("topic", "")
        difficulty = data.get("difficulty", "easy")
        count = data.get("count", 3)
        lang = data.get("language", i18n.get_language())
        result = lesson_gen.generate_exercise(
            topic, difficulty=difficulty, count=count, language=lang
        )
        if result.success:
            return jsonify({"success": True, "content": result.data})
        return jsonify({"success": False, "error": result.error}), 500

    @app.route("/api/courses", methods=["GET"])
    def api_courses():
        stats = registry.get_stats()
        categories = registry.get_categories()
        courses = {}
        for cat in categories:
            kps = registry.get_knowledge_points_by_category(cat)
            courses[cat] = [
                {"id": kp.id, "name": kp.name, "name_cn": kp.name_cn, "level": kp.level}
                for kp in kps
            ]
        return jsonify(
            {
                "stats": stats,
                "courses": courses,
            }
        )

    @app.route("/api/visualize/<viz_type>", methods=["POST"])
    def api_visualize(viz_type):
        data = request.json or {}

        if viz_type == "number_line":
            result = Visualizer.plot_number_line(
                start=data.get("start", -10),
                end=data.get("end", 10),
                highlight=data.get("highlight"),
                title=data.get("title", "Number Line"),
            )
        elif viz_type == "function":
            import numpy as np

            func_str = data.get("function", "x**2")
            try:
                func = _safe_eval_function(func_str)
                if func is None:
                    return jsonify({
                        "success": False,
                        "error": "Invalid function expression. Only basic math operations are allowed."
                    }), 400
                result = Visualizer.plot_function(
                    func,
                    x_range=tuple(data.get("x_range", [-10, 10])),
                    title=data.get("title", func_str),
                )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400
        elif viz_type == "bar":
            result = Visualizer.plot_bar(
                categories=data.get("categories", []),
                values=data.get("values", []),
                title=data.get("title", "Bar Chart"),
            )
        elif viz_type == "histogram":
            import numpy as np

            data_points = data.get("data", np.random.randn(1000).tolist())
            result = Visualizer.plot_histogram(
                np.array(data_points),
                bins=data.get("bins", 30),
                title=data.get("title", "Histogram"),
            )
        elif viz_type == "matrix":
            import numpy as np

            matrix_data = data.get("matrix", [[1, 2], [3, 4]])
            result = Visualizer.plot_matrix(
                np.array(matrix_data),
                title=data.get("title", "Matrix"),
            )
        else:
            return jsonify(
                {"success": False, "error": f"Unknown visualization type: {viz_type}"}
            ), 400

        if result.success:
            return jsonify(
                {"success": True, "data": result.data, "metadata": result.metadata}
            )
        return jsonify({"success": False, "error": result.error}), 500

    @app.route("/api/config", methods=["GET"])
    def api_get_config():
        return jsonify(
            {
                "active_provider": cfg.active_provider,
                "active_model": cfg.active_model,
                "language": i18n.get_language(),
            }
        )

    @app.route("/api/config", methods=["POST"])
    def api_set_config():
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        # Validate input
        schema = {
            "active_provider": (_validate_provider, False, None),
            "active_model": (_safe_str, False, None),
            "language": (_validate_language, False, None),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        if "active_provider" in validated:
            cfg.active_provider = validated["active_provider"]
        if "active_model" in validated:
            cfg.active_model = validated["active_model"]
        if "language" in validated:
            i18n.set_language(validated["language"])
            session["language"] = validated["language"]
            cfg.language = validated["language"]
        cfg.save()
        return jsonify({"success": True})

    @app.route("/api/language", methods=["GET"])
    def api_languages():
        return jsonify(
            {
                "current": i18n.get_language(),
                "supported": {
                    code: info["native"] for code, info in SUPPORTED_LANGUAGES.items()
                },
            }
        )

    @app.route("/api/language", methods=["POST"])
    def api_set_language():
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "language": (_validate_language, True, "zh"),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        lang = validated["language"]
        i18n.set_language(lang)
        session["language"] = lang
        cfg.language = lang
        cfg.save()
        return jsonify({"success": True, "language": lang})

    @app.route("/api/research", methods=["POST"])
    def api_research():
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "query": (_safe_str, True, ""),
            "depth": (_validate_depth, False, "medium"),
            "include_code": (bool, False, True),
            "include_visualization": (bool, False, True),
            "include_literature": (bool, False, True),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        query = validated["query"]
        depth = validated["depth"]
        include_code = validated["include_code"]
        include_viz = validated["include_visualization"]
        include_lit = validated["include_literature"]
        lang = validated["language"]

        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        result = research_engine.research(
            query=query,
            language=lang,
            depth=depth,
            include_code=include_code,
            include_visualization=include_viz,
            include_literature=include_lit,
        )

        return jsonify(
            {
                "success": True,
                "topic": result.topic,
                "summary": result.summary,
                "literature_review": result.literature_review,
                "papers": result.papers,
                "mathematical_derivation": result.mathematical_derivation,
                "experiments": result.experiments,
                "references": result.references,
                "full_report": result.full_report,
                "metadata": result.metadata,
            }
        )

    @app.route("/api/research/history", methods=["GET"])
    def api_research_history():
        history = research_engine.get_research_history()
        return jsonify({"success": True, "history": history})

    @app.route("/api/research/<filename>", methods=["GET"])
    def api_load_research(filename):
        result = research_engine.load_research(filename)
        if result:
            return jsonify({"success": True, "data": result})
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.route("/api/batch", methods=["POST"])
    def api_batch_process():
        """Batch processing endpoint for multiple operations."""
        data = request.json
        if not isinstance(data, dict) or "operations" not in data:
            return jsonify({"success": False, "error": "Operations list required"}), 400
        
        operations = data["operations"]
        if not isinstance(operations, list) or len(operations) > 10:  # Limit batch size
            return jsonify({"success": False, "error": "Operations must be a list with max 10 items"}), 400

        results = []
        for op in operations:
            if not isinstance(op, dict) or "type" not in op:
                results.append({"success": False, "error": "Each operation must have a type"})
                continue
                
            op_type = op.get("type")
            op_data = op.get("data", {})
            
            try:
                if op_type == "research":
                    # Perform research operation
                    query = op_data.get("query", "")
                    depth = op_data.get("depth", "medium")
                    lang = op_data.get("language", i18n.get_language())
                    
                    result = research_engine.research(
                        query=query,
                        language=lang,
                        depth=depth,
                        include_code=op_data.get("include_code", True),
                        include_visualization=op_data.get("include_visualization", True),
                        include_literature=op_data.get("include_literature", True),
                    )
                    results.append({
                        "success": result.success,
                        "data": result.data if result.success else result.error,
                        "operation": "research"
                    })
                elif op_type == "visualize":
                    # Perform visualization operation
                    viz_type = op_data.get("type", "function")
                    viz_params = {k: v for k, v in op_data.items() if k != "type"}
                    
                    result = visualizer.plot(viz_type, **viz_params)
                    results.append({
                        "success": result.success,
                        "data": result.data if result.success else result.error,
                        "operation": "visualize"
                    })
                elif op_type == "lesson":
                    # Generate lesson
                    lesson_topic = op_data.get("topic", "")
                    level = op_data.get("level", "beginner")
                    
                    result = lesson_gen.generate_lesson(lesson_topic, level)
                    results.append({
                        "success": result.success,
                        "data": result.data if result.success else result.error,
                        "operation": "lesson"
                    })
                else:
                    results.append({"success": False, "error": f"Unknown operation type: {op_type}", "operation": op_type})
            except Exception as e:
                results.append({"success": False, "error": str(e), "operation": op_type})
        
        return jsonify({"success": True, "results": results})

    @app.route("/api/async/research", methods=["POST"])
    def api_async_research():
        """Asynchronous research endpoint that returns immediately."""
        import threading
        import uuid
        from datetime import datetime
        
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "query": (_safe_str, True, ""),
            "depth": (_validate_depth, False, "medium"),
            "include_code": (bool, False, True),
            "include_visualization": (bool, False, True),
            "include_literature": (bool, False, True),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Store task status (in a real app, this would use Redis or database)
        if not hasattr(api_async_research, '_tasks'):
            api_async_research._tasks = {}
        
        api_async_research._tasks[task_id] = {
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "params": validated
        }
        
        # Start background thread for processing
        def run_research_task(task_id, params):
            api_async_research._tasks[task_id]["status"] = "processing"
            try:
                result = research_engine.research(
                    query=params["query"],
                    language=params["language"],
                    depth=params["depth"],
                    include_code=params["include_code"],
                    include_visualization=params["include_visualization"],
                    include_literature=params["include_literature"],
                )
                api_async_research._tasks[task_id].update({
                    "status": "completed",
                    "result": result.data if result.success else result.error,
                    "success": result.success,
                    "completed_at": datetime.now().isoformat()
                })
            except Exception as e:
                api_async_research._tasks[task_id].update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                })
        
        thread = threading.Thread(
            target=run_research_task,
            args=(task_id, validated)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "status": "queued"
        })

    @app.route("/api/async/research/<task_id>", methods=["GET"])
    def api_async_research_status(task_id):
        """Get status of async research task."""
        if not hasattr(api_async_research, '_tasks') or task_id not in api_async_research._tasks:
            return jsonify({"success": False, "error": "Task not found"}), 404
        
        task = api_async_research._tasks[task_id]
        
        response = {
            "task_id": task_id,
            "status": task["status"],
            "created_at": task["created_at"]
        }
        
        if task["status"] == "completed":
            response.update({
                "success": task.get("success", False),
                "result": task.get("result"),
                "completed_at": task.get("completed_at")
            })
        elif task["status"] == "failed":
            response.update({
                "error": task.get("error"),
                "completed_at": task.get("completed_at")
            })
        
        return jsonify(response)

    # Learning tracker endpoints
    def get_user_tracker():
        """Get learning tracker for current user session."""
        user_id = session.get("user_id", "anonymous")
        return LearningTracker(user_id=user_id)

    @app.route("/api/progress", methods=["GET"])
    def api_get_progress():
        """Get user learning progress."""
        tracker = get_user_tracker()
        return jsonify({
            "success": True,
            "progress": tracker.get_progress_summary(),
            "achievements": tracker.get_achievements()
        })

    @app.route("/api/progress/lesson", methods=["POST"])
    def api_track_lesson():
        """Track lesson completion."""
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "lesson_id": (_safe_str, True, ""),
            "category": (_safe_str, True, ""),
            "level": (_safe_str, True, ""),
            "action": (lambda x: x if x in ["start", "complete"] else _raise_value_error("action must be start or complete"), True, "complete"),
            "time_taken": (_safe_int_range(0, 36000), False, 0),  # Max 10 hours
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        tracker = get_user_tracker()
        
        if validated["action"] == "start":
            tracker.start_lesson(
                validated["lesson_id"], 
                validated["category"], 
                validated["level"]
            )
        elif validated["action"] == "complete":
            tracker.complete_lesson(
                validated["lesson_id"],
                validated["category"], 
                validated["level"],
                validated["time_taken"]
            )
        
        return jsonify({"success": True})

    @app.route("/api/recommendations", methods=["GET"])
    def api_get_recommendations():
        """Get personalized study recommendations."""
        tracker = get_user_tracker()
        recommendations = tracker.get_study_recommendations()
        return jsonify({
            "success": True,
            "recommendations": recommendations
        })

    @app.route("/api/math/prove", methods=["POST"])
    def api_math_prove():
        """Prove a mathematical theorem."""
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "theorem": (_safe_str, True, ""),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        result = math_reasoning.prove_theorem(
            theorem=validated["theorem"],
            language=validated["language"]
        )
        
        return jsonify({
            "success": result.success,
            "response": result.response,
            "steps": result.steps,
            "verification": result.verification,
            "confidence": result.confidence,
            "symbolic_checks": [
                {"claim": c.claim, "verified": c.verified, "method": c.method, "detail": c.detail, "confidence": c.confidence}
                for c in (result.symbolic_checks or [])
            ],
            "self_consistent": result.self_consistent,
            "error": result.error
        })

    @app.route("/api/math/solve", methods=["POST"])
    def api_math_solve():
        """Solve a mathematical problem."""
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "problem": (_safe_str, True, ""),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        result = math_reasoning.solve_problem(
            problem=validated["problem"],
            language=validated["language"]
        )
        
        return jsonify({
            "success": result.success,
            "response": result.response,
            "steps": result.steps,
            "verification": result.verification,
            "confidence": result.confidence,
            "symbolic_checks": [
                {"claim": c.claim, "verified": c.verified, "method": c.method, "detail": c.detail, "confidence": c.confidence}
                for c in (result.symbolic_checks or [])
            ],
            "self_consistent": result.self_consistent,
            "error": result.error
        })

    @app.route("/api/math/analyze", methods=["POST"])
    def api_math_analyze():
        """Analyze a mathematical conjecture."""
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "conjecture": (_safe_str, True, ""),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        result = math_reasoning.analyze_conjecture(
            conjecture=validated["conjecture"],
            language=validated["language"]
        )
        
        return jsonify({
            "success": result.success,
            "response": result.response,
            "steps": result.steps,
            "verification": result.verification,
            "confidence": result.confidence,
            "symbolic_checks": [
                {"claim": c.claim, "verified": c.verified, "method": c.method, "detail": c.detail, "confidence": c.confidence}
                for c in (result.symbolic_checks or [])
            ],
            "self_consistent": result.self_consistent,
            "error": result.error
        })

    @app.route("/api/math/compute", methods=["POST"])
    def api_math_compute():
        """Perform symbolic computation."""
        data = request.json
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be JSON object"}), 400
        
        schema = {
            "expression": (_safe_str, True, ""),
            "language": (_validate_language, False, i18n.get_language()),
        }
        validated, error = _validate_input(data, schema)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        result = math_reasoning.symbolic_computation(
            expression=validated["expression"],
            language=validated["language"]
        )
        
        return jsonify({
            "success": result.success,
            "response": result.response,
            "steps": result.steps,
            "verification": result.verification,
            "confidence": result.confidence,
            "symbolic_checks": [
                {"claim": c.claim, "verified": c.verified, "method": c.method, "detail": c.detail, "confidence": c.confidence}
                for c in (result.symbolic_checks or [])
            ],
            "self_consistent": result.self_consistent,
            "error": result.error
        })

    return app


def run_web(host="127.0.0.1", port=5000, debug=False):
    """Run the web application."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web()
