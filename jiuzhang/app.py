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


def create_app(config: Config = None):
    """Create Flask application with i18n support."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("JIUZHANG_SECRET", "jiuzhang-dev-secret")
    CORS(app)

    cfg = config or Config()
    client = MultiProviderClient(cfg)
    lesson_gen = LessonGenerator(cfg)
    registry = CourseRegistry()
    curriculum = registry.build_curriculum()
    i18n = I18n(default_language=cfg.language)
    research_engine = ResearchEngine(cfg)

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
                func = eval(
                    f"lambda x: {func_str}",
                    {
                        "np": np,
                        "sin": np.sin,
                        "cos": np.cos,
                        "exp": np.exp,
                        "sqrt": np.sqrt,
                    },
                )
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

            data_points = data.get(
                "data", __import__("numpy").random.randn(1000).tolist()
            )
            result = Visualizer.plot_histogram(
                __import__("numpy").array(data_points),
                bins=data.get("bins", 30),
                title=data.get("title", "Histogram"),
            )
        elif viz_type == "matrix":
            import numpy as np

            matrix_data = data.get("matrix", [[1, 2], [3, 4]])
            result = Visualizer.plot_matrix(
                __import__("numpy").array(matrix_data),
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
        if "active_provider" in data:
            cfg.active_provider = data["active_provider"]
        if "active_model" in data:
            cfg.active_model = data["active_model"]
        if "language" in data:
            i18n.set_language(data["language"])
            session["language"] = data["language"]
            cfg.language = data["language"]
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
        lang = data.get("language", "zh")
        if lang in SUPPORTED_LANGUAGES:
            i18n.set_language(lang)
            session["language"] = lang
            cfg.language = lang
            cfg.save()
            return jsonify({"success": True, "language": lang})
        return jsonify({"success": False, "error": "Unsupported language"}), 400

    @app.route("/api/research", methods=["POST"])
    def api_research():
        data = request.json
        query = data.get("query", "")
        depth = data.get("depth", "medium")
        include_code = data.get("include_code", True)
        include_viz = data.get("include_visualization", True)
        include_lit = data.get("include_literature", True)
        lang = data.get("language", i18n.get_language())

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

    return app


def run_web(host="127.0.0.1", port=5000, debug=False):
    """Run the web application."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web()
