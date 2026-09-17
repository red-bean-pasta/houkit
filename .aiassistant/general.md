---
apply: always
---

> You must follow these rules and carry them out through the whole conversation.

# Background
This project hubs some common python utility methods for Houdini Object Model (HOM). The API module in Python is `hou`. The executable is `hython`. It's encouraged to write reusable methods, helper methods, wrapper methods. Even if a method isn't reused, breaking one "god" method into multiple methods helps self-documenting and clean up logic. 

# Other coding conventions
No need for over-defensiveness. `assert` is natively supported in HOM. Keep the code concise. By "concise", I don't mean use a lot of abbreviations or inappropriate one-liners, but no boilerplate and repetitiveness. Make the code easy to understand. New lines should be used mainly for logical grouping rather than viewport carriage. You can add comments to annotate a code block. You can use abbreviations for variable naming if the method is modular and short. You can add comment behind the variable to annotate the full name at its first appearence.
You can start out a task by a "just-work" method caring nothing about commenting, logical grouping and modularity, then refactor it into a code block that's clear, modular, logically comprehensive to human user. I believe you know what gives a bad block of code, like repetitive pattern and hardcoding. 
Put helper and modular methods after the parent method instead of before it. This is because users usually read from the top, therefore higher position means more importance. If two parent methods share the same child method, put it at the last of the script. This new line convention is mandatory.

# Other agent instructions
You don't need to over-think. If the task is simple, you can simply do it. It's also encouraged to adopt the "inspect code + write code + try + error + debug" than "inspect files". You don't need to be 100% confident before making changes.
Many of the time, your operations are prompted to user by ACP or MCP. You can always comment the intention, so that the user has a better understanding on what stage we are at and approve the tool use.
You can always actively raise questions for clarification and require answer for multiple choices. The user may not write the best instruction, clarify their need enough and may have typos and reference errors, you can always point them out and ask for clarification. 
For file editing, prefer ACP tool `client_edit_file`. It's discouraged to use `apply_patch`, `pycharm_execute_terminal_command` and python's `file.write` because their formatting is hard for user to inspect. 
You can use `sed` or `head` for file segmentation. But if you don't know the exact position, you can cat the whole file, or identify it first using grep. Do not use sed to "nudge" along the file because the user may get frustrated. You can also combine multiple commands into one to save turns and tokens.
You can use MCP or `python.read` to read out-of-scope files.
No Latex Output. Use only MarkDown. LaTex have problem rendering in PyCharm.
You can use git stash, commit and branch. But those are quite powerful moves so always clarify your intent then ask for permit. 
Response when you are confident enough. Don't be paranoid and spend forever verifying or inspecting. Those efforts are not appreciated.
You can always record your thoughts, findings, summaries or any other necessary stuff to `.aiassistant/tmp/`, if it helps your work.

# Modes 
An agent like you have different thinking chains and preparation steps given a task. Most of the time, they involve reading existing codes, inspecting models, planning steps, apply edits, verify results and output summary. They are often a bit rigid. Therefore, the user can specify three modes:
- [All Allowed]: No restriction. Do what you think you need to do.
- [Minimal Pre]: Preparations should be kept simple. You can only do vital inspections. Making edits and verification are unrestricted. This mode is commonly used when the instruction is very clear and detailed, the code block is already halfly finished and statically guessable, or when the task is just very simple. Note that the user can get frustrated and reject tool uses in this mode. In this mode, you should make assumptions agressively, and be error-led instead of plan-led. For example, you should assume the file exists, the specs are correct, everything is in place, and your edits are correct.
- [Static Pre]: Tool calls are mostly unallowed except reading necessary codes. All inference and inspection must be made on codes, like you are no longer an agent but a chat window. However, post verification and test is not restricted.
- [Minimal Post]: Post verification and test should be kept simple, or even skipped. This mode is commonly used when the changes are local and small, the edits are unlikely to go wrong, the greater picture isn't totally finished, or the user want to inspect themselves. 
- [No Post]: Simply skip post verification and test.
- [Quicky]: Output as quick as possible. Common in simple and local method. You can think of it as [Static Pre] + [Minimal Post]. This mode resembles much more with traditional chat window, and expects limited even insufficient information, and more aggressive assumption and inference.

It may actually help you to give better output by determining a mode for each quest yourself, so you can choose actually one if the user didn't specify.
By default, the mode should be [Static Pre] if neither of you and the user specified.
Output the mode at the beginning of every of your response, whether already specified, pretty obvious or not.

# To iterate
- break down methods
- use assert
- raise on questions
- prefer ACP tools
- don't overthink
- `.aiassistant/tmp/` is your notebook
- modes like [static pre]
