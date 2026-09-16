const DEFAULT_SCALE = 4;

function positiveNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : fallback;
}

function dimensionsFor(svg) {
  const viewBox = String(svg.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number);
  if (viewBox.length === 4 && viewBox.every(Number.isFinite)) {
    return { width: positiveNumber(viewBox[2], 1200), height: positiveNumber(viewBox[3], 600) };
  }
  return {
    width: positiveNumber(svg.getAttribute("width"), svg.clientWidth || 1200),
    height: positiveNumber(svg.getAttribute("height"), svg.clientHeight || 600)
  };
}

function pageStyles() {
  if (typeof document === "undefined") return "";
  return Array.from(document.styleSheets).flatMap(sheet => {
    try {
      return Array.from(sheet.cssRules || []).map(rule => rule.cssText);
    } catch {
      return [];
    }
  }).join("\n");
}

function serializedSvg(svg, width, height) {
  const clone = svg.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  clone.setAttribute("style", "background:#ffffff");
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = pageStyles();
  clone.insertBefore(style, clone.firstChild);
  return new XMLSerializer().serializeToString(clone);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename.endsWith(".png") ? filename : `${filename}.png`;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

/**
 * Rasterizes an SVG Figure to a white-background, high-resolution PNG.
 * The export intentionally excludes surrounding HTML controls because only
 * the SVG node is serialized.
 */
export function exportSvgAsPng(svg, filename, options = {}) {
  if (!svg) return Promise.reject(new Error("Chart SVG is not available"));
  if (typeof XMLSerializer === "undefined" || typeof Image === "undefined" || typeof document === "undefined") {
    return Promise.reject(new Error("PNG export is only available in a browser"));
  }

  const { width, height } = dimensionsFor(svg);
  const scale = positiveNumber(options.scale, DEFAULT_SCALE);
  const serialized = serializedSvg(svg, width, height);
  const blob = new Blob([serialized], { type: "image/svg+xml;charset=utf-8" });
  const sourceUrl = URL.createObjectURL(blob);

  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Canvas 2D context is unavailable");
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(png => {
          if (!png) {
            reject(new Error("Unable to create PNG"));
            return;
          }
          downloadBlob(png, filename);
          resolve(png);
        }, "image/png");
      } catch (error) {
        reject(error);
      } finally {
        URL.revokeObjectURL(sourceUrl);
      }
    };
    image.onerror = () => {
      URL.revokeObjectURL(sourceUrl);
      reject(new Error("Unable to render chart SVG"));
    };
    image.src = sourceUrl;
  });
}
