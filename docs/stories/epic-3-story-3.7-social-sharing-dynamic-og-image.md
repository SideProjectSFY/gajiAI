# Story 3.7: Social Sharing with Dynamic og:image Generation

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.7
**Priority**: P2 - Medium  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Generate dynamic Open Graph images for scenario sharing on social media using Puppeteer to render custom HTML templates. Include share buttons for Twitter, Facebook, and direct link copy with rich preview metadata.

## Dependencies

**Blocks**:

- None (enhances virality)

**Requires**:

- Story 3.1: Scenario Browse UI (scenarios to share)
- Story 1.1: Scenario Data Model (scenario data for image generation)

## Acceptance Criteria

- [ ] Share button dropdown on scenario cards: Twitter, Facebook, Copy Link
- [ ] Dynamic `og:image` generation service using Puppeteer
- [ ] Image template renders: scenario title, parameters, base story, quality score
- [ ] Images cached in `/public/og-images/{scenario_id}.png` (served by Nginx)
- [ ] Meta tags injected server-side for social crawlers: `og:title`, `og:description`, `og:image`, `og:url`
- [ ] Image generation triggered on scenario creation/update
- [ ] Fallback to default image if generation fails
- [ ] Copy Link shows toast: "Link copied with preview!"
- [ ] Twitter/Facebook share opens in new window with pre-filled text
- [ ] Image dimensions: 1200x630 (optimal for all platforms)
- [ ] Unit tests >80% coverage

## Technical Notes

**OG Image Generation Service (Backend)**:

```java
@Service
public class OgImageService {

    private static final String IMAGE_DIR = "public/og-images/";
    private static final String PUPPETEER_SCRIPT = "scripts/generate-og-image.js";

    @Value("${app.base-url}")
    private String baseUrl;

    public String generateOgImage(Scenario scenario) {
        String filename = scenario.getId().toString() + ".png";
        String outputPath = IMAGE_DIR + filename;

        // Check if image already exists
        File imageFile = new File(outputPath);
        if (imageFile.exists()) {
            return baseUrl + "/og-images/" + filename;
        }

        try {
            // Prepare data for Puppeteer script
            ObjectMapper mapper = new ObjectMapper();
            String scenarioJson = mapper.writeValueAsString(Map.of(
                "title", buildScenarioTitle(scenario),
                "baseStory", scenario.getBaseStory(),
                "parameters", scenario.getParameters(),
                "qualityScore", scenario.getQualityScore(),
                "createdBy", scenario.getCreatedBy().getUsername()
            ));

            // Execute Puppeteer script
            ProcessBuilder pb = new ProcessBuilder(
                "node",
                PUPPETEER_SCRIPT,
                scenarioJson,
                outputPath
            );
            pb.redirectErrorStream(true);
            Process process = pb.start();

            int exitCode = process.waitFor();
            if (exitCode != 0) {
                String error = new BufferedReader(new InputStreamReader(process.getInputStream()))
                    .lines().collect(Collectors.joining("\n"));
                throw new RuntimeException("Puppeteer failed: " + error);
            }

            return baseUrl + "/og-images/" + filename;
        } catch (Exception e) {
            log.error("Failed to generate OG image for scenario {}", scenario.getId(), e);
            return baseUrl + "/og-images/default.png"; // Fallback
        }
    }

    private String buildScenarioTitle(Scenario scenario) {
        String type = scenario.getScenarioType().toString().replace("_", " ");
        return String.format("What if... [%s]", type);
    }
}
```

**Puppeteer Script (Node.js)**:

```javascript
// scripts/generate-og-image.js
const puppeteer = require("puppeteer");
const fs = require("fs");

async function generateOgImage(scenarioData, outputPath) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630 });

  // HTML template for OG image
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          width: 1200px;
          height: 630px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }
        .container {
          width: 90%;
          height: 90%;
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 20px;
          padding: 60px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }
        .logo {
          font-size: 32px;
          font-weight: 700;
          opacity: 0.9;
        }
        .title {
          font-size: 48px;
          font-weight: 700;
          margin-bottom: 20px;
          line-height: 1.2;
        }
        .base-story {
          font-size: 24px;
          opacity: 0.9;
          margin-bottom: 30px;
        }
        .parameters {
          font-size: 20px;
          opacity: 0.8;
          line-height: 1.6;
        }
        .footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 18px;
        }
        .quality-badge {
          background: rgba(255, 255, 255, 0.3);
          padding: 10px 20px;
          border-radius: 50px;
          font-weight: 600;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">📖 Gaji - What If?</div>
        
        <div class="content">
          <div class="title">${scenarioData.title}</div>
          <div class="base-story">${scenarioData.baseStory}</div>
          <div class="parameters">
            ${Object.entries(scenarioData.parameters)
              .map(([key, value]) => `<div>• ${key}: ${value}</div>`)
              .join("")}
          </div>
        </div>

        <div class="footer">
          <div>Created by @${scenarioData.createdBy}</div>
          <div class="quality-badge">⭐ ${scenarioData.qualityScore.toFixed(
            1
          )}/10</div>
        </div>
      </div>
    </body>
    </html>
  `;

  await page.setContent(html);
  await page.screenshot({ path: outputPath, type: "png" });
  await browser.close();
}

// Main execution
const scenarioData = JSON.parse(process.argv[2]);
const outputPath = process.argv[3];

generateOgImage(scenarioData, outputPath)
  .then(() => {
    console.log("OG image generated successfully");
    process.exit(0);
  })
  .catch((err) => {
    console.error("Error generating OG image:", err);
    process.exit(1);
  });
```

**Meta Tag Injection (Server-Side Rendering)**:

```java
@Controller
public class ScenarioViewController {

    @Autowired
    private ScenarioService scenarioService;

    @Autowired
    private OgImageService ogImageService;

    @GetMapping("/scenarios/{id}")
    public String viewScenario(@PathVariable UUID id, Model model) {
        Scenario scenario = scenarioService.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Scenario not found"));

        // Generate OG image
        String ogImageUrl = ogImageService.generateOgImage(scenario);

        // Add meta tags to model
        model.addAttribute("ogTitle", buildScenarioTitle(scenario));
        model.addAttribute("ogDescription", buildScenarioDescription(scenario));
        model.addAttribute("ogImage", ogImageUrl);
        model.addAttribute("ogUrl", "https://gaji.app/scenarios/" + id);

        return "scenario-detail";
    }

    private String buildScenarioTitle(Scenario scenario) {
        return String.format("What if... %s", scenario.getBaseStory());
    }

    private String buildScenarioDescription(Scenario scenario) {
        Map<String, Object> params = scenario.getParameters();
        if (scenario.getScenarioType() == ScenarioType.CHARACTER_CHANGE) {
            return String.format("%s is %s instead of %s",
                params.get("character"),
                params.get("new_property"),
                params.get("original_property"));
        } else if (scenario.getScenarioType() == ScenarioType.EVENT_ALTERATION) {
            return String.format("Explore a timeline where %s", params.get("altered_outcome"));
        } else {
            return String.format("Imagine %s in %s", scenario.getBaseStory(), params.get("new_setting"));
        }
    }
}
```

**HTML Template with Meta Tags**:

```html
<!-- templates/scenario-detail.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <!-- Open Graph Meta Tags -->
    <meta property="og:type" content="article" />
    <meta property="og:title" th:content="${ogTitle}" />
    <meta property="og:description" th:content="${ogDescription}" />
    <meta property="og:image" th:content="${ogImage}" />
    <meta property="og:url" th:content="${ogUrl}" />
    <meta property="og:site_name" content="Gaji - What If?" />

    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" th:content="${ogTitle}" />
    <meta name="twitter:description" th:content="${ogDescription}" />
    <meta name="twitter:image" th:content="${ogImage}" />

    <title th:text="${ogTitle}">Scenario Detail</title>
  </head>
  <body>
    <!-- Vue app mounts here -->
    <div id="app"></div>
  </body>
</html>
```

**Frontend Share Component**:

```vue
<template>
  <div class="share-button-group">
    <button @click="toggleDropdown" class="share-btn">
      <ShareIcon /> Share
    </button>

    <transition name="fade">
      <div v-if="dropdownOpen" class="share-dropdown">
        <button @click="shareTwitter" class="share-option">
          <TwitterIcon /> Share on Twitter
        </button>
        <button @click="shareFacebook" class="share-option">
          <FacebookIcon /> Share on Facebook
        </button>
        <button @click="copyLink" class="share-option">
          <LinkIcon /> Copy Link
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = defineProps(["scenario"]);
const dropdownOpen = ref(false);

const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value;
};

const shareTwitter = () => {
  const text = `What if... ${props.scenario.baseStory}? 🤔`;
  const url = `https://gaji.app/scenarios/${props.scenario.id}`;
  window.open(
    `https://twitter.com/intent/tweet?text=${encodeURIComponent(
      text
    )}&url=${encodeURIComponent(url)}`,
    "_blank",
    "width=550,height=420"
  );
  dropdownOpen.value = false;
};

const shareFacebook = () => {
  const url = `https://gaji.app/scenarios/${props.scenario.id}`;
  window.open(
    `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    "_blank",
    "width=550,height=420"
  );
  dropdownOpen.value = false;
};

const copyLink = async () => {
  const url = `https://gaji.app/scenarios/${props.scenario.id}`;
  try {
    await navigator.clipboard.writeText(url);
    showToast("Link copied with preview! 🎉");
  } catch (error) {
    // Fallback for older browsers
    const input = document.createElement("input");
    input.value = url;
    document.body.appendChild(input);
    input.select();
    document.execCommand("copy");
    document.body.removeChild(input);
    showToast("Link copied!");
  }
  dropdownOpen.value = false;
};
</script>
```

## QA Checklist

### Functional Testing

- [ ] Share button opens dropdown with 3 options
- [ ] Twitter share opens with pre-filled text and URL
- [ ] Facebook share opens with scenario URL
- [ ] Copy Link copies URL to clipboard
- [ ] OG image generated on scenario creation
- [ ] Meta tags correctly injected in HTML
- [ ] Social crawlers (Facebook Debugger, Twitter Card Validator) show rich preview

### Image Generation Testing

- [ ] Puppeteer generates 1200x630 PNG image
- [ ] Image template renders all scenario data correctly
- [ ] Quality score badge displays correctly
- [ ] Fallback image used if generation fails
- [ ] Images cached (not regenerated on every share)
- [ ] Old images cleaned up after scenario update

### Performance

- [ ] Image generation completes < 3 seconds
- [ ] Cached images served < 50ms
- [ ] Share button dropdown opens < 100ms
- [ ] No blocking on main thread during generation

### Cross-Platform Testing

- [ ] Twitter preview shows correct image/title/description
- [ ] Facebook preview shows correct image/title/description
- [ ] LinkedIn preview works correctly
- [ ] Discord embed shows rich preview
- [ ] Image renders correctly on mobile/desktop

### Accessibility & Security

- [ ] Share buttons keyboard accessible
- [ ] ARIA labels on share options
- [ ] Image generation sanitizes user input (XSS prevention)
- [ ] Rate limit on image generation (prevent abuse)

## Estimated Effort

10 hours
