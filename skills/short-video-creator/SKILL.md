# short-video-creator

## Overview
Creates short AI-generated video clips from text prompts using Puter.js.

## Workflow
1. Extract prompt from user request.
2. Create an HTML file with Puter.js (https://js.puter.com/v2/).
3. Use puter.ai.txt2vid() with model wan-ai/wan2.7-t2v.
4. Save the HTML file to channel/web/static/assets/video/.

## Code Example
<script src="https://js.puter.com/v2/"></script>
<script>
  puter.ai.txt2vid("A futuristic city at night", { model: "wan-ai/wan2.7-t2v" }).then(video => {
    document.body.appendChild(video);
    video.play();
  });
</script>
