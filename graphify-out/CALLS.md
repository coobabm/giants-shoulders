# 跨模块调用表（自动生成，别手改）

由 `engine/tools/agent_map.py` 用 Python ast 生成：`模块.函数()` 形式的跨模块调用。改了函数签名 / 删函数之前，先看这里谁在调它。

## agentsview.py
- `_get()` ← `deep._cwds`
- `alive()` ← `__main__.cmd_status`, `page.build`
- `sessions()` ← `__main__.cmd_collect`, `page.build`
- `ts()` ← `__main__.cmd_collect`, `deep.plan`, `deep.run`, `page._iso_ts`
- `user_prompts()` ← `__main__.cmd_collect`, `deep._prompts`, `page.build`

## auth.py
- `base_url()` ← `server.do_GET`
- `clear_key()` ← `__main__.cmd_auth`, `server.do_POST`
- `info()` ← `server.settings`
- `list_models()` ← `server.do_GET`
- `mode()` ← `server.do_POST`
- `run()` ← `codeagent._run`, `llm.ask`
- `save_key()` ← `__main__.cmd_auth`, `server.do_POST`
- `set_base_url()` ← `server.do_POST`
- `set_mode()` ← `__main__.cmd_auth`, `server.do_POST`
- `status()` ← `__main__.cmd_auth`, `__main__.cmd_status`

## codeagent.py
- `_run()` ← `deep._read_code`
- `analyze_project()` ← `pipeline._dive_project`
- `analyze_repo()` ← `pipeline._dive_repo`
- `is_project()` ← `deep._project_of`, `pipeline.process`

## config.py
- `model()` ← `__main__.cmd_annotate`, `__main__.cmd_auth`, `codeagent._run`, `deep.plan`, `deep.run`, `deep.score_missing`, `group.update`, `pipeline.process`, `server.do_POST`, `server.settings`
- `save_models()` ← `server.do_POST`
- `save_settings()` ← `server.do_POST`
- `setting()` ← `deep.plan`, `deep.run`, `server.settings`

## context.py
- `risk_flags()` ← `pipeline.process`

## deep.py
- `plan()` ← `server.do_GET`
- `run()` ← `__main__.cmd_deep`, `server._deep`
- `score_missing()` ← `__main__.cmd_annotate`
- `set_root()` ← `server.do_POST`
- `set_todo()` ← `server.do_POST`, `server.launch`
- `todo_prompt()` ← `server.do_GET`

## gate.py
- `maybe_build()` ← `__main__.cmd_collect`

## github.py
- `canary()` ← `deep.run`, `pipeline.process`
- `channel_status()` ← `deep.run`, `pipeline.process`
- `log_entry()` ← `deep._meta`, `deep._search`
- `readmes()` ← `pipeline.process`
- `repo_meta()` ← `pipeline.process`

## group.py
- `load()` ← `deep._task`, `deep.run`, `deep.set_root`, `page.build`, `server.do_GET`, `server.start_deep`
- `reset()` ← `page.build`
- `save()` ← `deep.run`, `deep.set_root`, `server.start_deep`
- `update()` ← `page.build`

## local.py
- `match()` ← `pipeline.process`

## page.py
- `build()` ← `__main__.cmd_page`, `server.do_GET`

## pipeline.py
- `process()` ← `__main__._run_one`, `__main__.cmd_scan`

## rank.py
- `annotate()` ← `pipeline.process`
- `pick()` ← `pipeline.process`

## registries.py
- `select_sources()` ← `pipeline.process`

## repocache.py
- `fetch()` ← `pipeline._dive_repo`

## report_md.py
- `to_md()` ← `__main__.cmd_collect`, `__main__.cmd_deep`, `__main__.cmd_recent`, `__main__.cmd_scan`, `__main__.cmd_show`

## server.py
- `alive()` ← `__main__.cmd_page`
- `serve()` ← `__main__.cmd_serve`
- `url()` ← `__main__.cmd_page`

## sources.py
- `normalize()` ← `__main__.cmd_collect`, `__main__.cmd_scan`, `page._dedupe`

## store.py
- `add_also_in()` ← `__main__.cmd_collect`
- `add_report()` ← `__main__.cmd_collect`, `__main__.cmd_scan`, `deep.run`, `server.start_deep`
- `find_duplicate()` ← `__main__.cmd_collect`
- `get_meta()` ← `__main__.cmd_collect`, `group.load`, `sources.bootstrap`
- `get_offsets()` ← `sources.__init__`
- `get_report()` ← `__main__._run_one`, `__main__.cmd_deep`, `__main__.cmd_scan`, `__main__.cmd_show`, `deep._prev_deep`, `deep.run`, `deep.set_todo`, `deep.todo_prompt`, `page.build`, `server.do_GET`
- `list_reports()` ← `__main__.cmd_annotate`, `__main__.cmd_recent`, `deep._estimate`, `deep.score_missing`, `page.build`
- `q()` ← `__main__.cmd_scan`
- `recent_session_summaries()` ← `pipeline.process`
- `set_meta()` ← `__main__.cmd_collect`, `group.reset`, `group.save`, `sources.bootstrap`
- `set_offset()` ← `sources.bootstrap`, `sources.poll`
- `stats()` ← `__main__.cmd_status`, `page.build`
- `update_report()` ← `__main__.cmd_annotate`, `deep.run`, `deep.score_missing`, `deep.set_todo`, `pipeline.process`

## verdict.py
- `claims_absence()` ← `pipeline.process`
- `data_headline()` ← `pipeline.process`
- `floor_level()` ← `pipeline.process`
- `guard()` ← `pipeline.process`
