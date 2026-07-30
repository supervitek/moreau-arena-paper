(() => {
    "use strict";

    const DATA_URL = "/static/noir-track1-report-data.json";
    const systemGrid = document.getElementById("system-grid");
    const atlasSummary = document.getElementById("atlas-summary");
    const timeline = document.getElementById("evidence-timeline");
    const timelineToggle = document.getElementById("timeline-toggle");
    const sourceDocumentList = document.getElementById("source-document-list");
    const filterButtons = Array.from(document.querySelectorAll("[data-panel-filter]"));

    let reportData = null;
    let activePanel = "all";
    let allTimelineOpen = false;

    function element(tagName, className, text) {
        const node = document.createElement(tagName);
        if (className) {
            node.className = className;
        }
        if (text !== undefined && text !== null) {
            node.textContent = text;
        }
        return node;
    }

    function metric(label, value) {
        const cell = element("div", "distribution-cell");
        cell.append(element("span", "", label));
        cell.append(element("strong", "", value));
        return cell;
    }

    function renderSystems() {
        if (!reportData) {
            return;
        }

        const systems = reportData.systems.filter((system) => {
            return activePanel === "all" || system.panel === activePanel;
        });

        const completeProfiles = systems.filter((system) => system.tier === "Q3" || system.tier === "Q4").length;
        const partialProfiles = systems.filter((system) => system.tier === "Q2").length;
        const routeLimited = systems.filter((system) => system.tier === "Q1" || system.tier === "Q0").length;

        atlasSummary.replaceChildren();
        const summary = element("p");
        summary.append(
            element("strong", "", `${systems.length} systems shown`),
            document.createTextNode(` · ${completeProfiles} complete behavioral profiles · ${partialProfiles} Phase-0/partial profiles · ${routeLimited} route-limited profiles`)
        );
        atlasSummary.append(summary);

        systemGrid.replaceChildren();
        systems.forEach((system) => {
            const card = element("article", "system-card");
            card.dataset.panel = system.panel;

            const header = element("div", "system-card-header");
            const identity = element("div", "system-identity");
            const identityCopy = element("div");
            identityCopy.append(
                element("h3", "system-name", system.name),
                element("code", "system-model", system.model)
            );
            identity.append(identityCopy, element("span", "tier-badge", system.tier));
            header.append(identity, element("p", "system-provider", system.provider));

            const body = element("div", "system-card-body");
            const distribution = element("div", "distribution-row");
            distribution.append(
                metric("LOWER", system.lower === null ? "—" : String(system.lower)),
                metric("HIGHER", system.higher === null ? "—" : String(system.higher)),
                metric("A/B", system.divergence)
            );
            body.append(distribution, element("p", "system-description", system.description));

            const footer = element("div", "system-card-footer");
            footer.append(
                element("p", "system-classification", system.classification),
                element("p", "system-limitation", `Limit: ${system.limitation}`)
            );

            card.append(header, body, footer);
            systemGrid.append(card);
        });
    }

    function timelineStatusLabel(status) {
        if (status === "stop") {
            return "Preserved stop";
        }
        if (status === "freeze") {
            return "Zero-call freeze";
        }
        return "Accepted";
    }

    function renderTimeline() {
        if (!reportData) {
            return;
        }

        timeline.replaceChildren();
        reportData.timeline.forEach((stage, index) => {
            const item = element("article", "timeline-item");
            const indexNode = element("div", "timeline-index", String(index + 1).padStart(2, "0"));
            const content = element("div", "timeline-content");
            const summary = element("button", "timeline-summary");
            summary.type = "button";
            summary.setAttribute("aria-expanded", "false");

            const labelWrap = element("span");
            labelWrap.append(
                element("span", "timeline-label", stage.label),
                element("span", "timeline-protocol", stage.protocol)
            );

            const status = element("span", `timeline-status ${stage.status}`, timelineStatusLabel(stage.status));
            summary.append(labelWrap, element("span", "timeline-accounting", stage.accounting), status);

            const details = element("div", "timeline-details");
            const detailsGrid = element("div", "timeline-details-grid");
            const resultBlock = element("div");
            resultBlock.append(
                element("p", "", stage.detail),
                element("code", "", stage.classification)
            );
            const terminalBlock = element("div");
            terminalBlock.append(
                element("p", "", "Frozen terminal"),
                element("code", "", stage.terminal)
            );
            detailsGrid.append(resultBlock, terminalBlock);
            details.append(detailsGrid);

            summary.addEventListener("click", () => {
                const isOpen = item.classList.toggle("open");
                summary.setAttribute("aria-expanded", String(isOpen));
            });

            content.append(summary, details);
            item.append(indexNode, content);
            timeline.append(item);
        });
    }

    function renderSourceDocuments() {
        if (!reportData) {
            return;
        }

        sourceDocumentList.replaceChildren();
        reportData.sourceDocuments.forEach((documentRecord) => {
            const item = element("li");
            item.append(
                document.createTextNode(documentRecord.path),
                element("span", "", `SHA-256 ${documentRecord.sha256}`)
            );
            sourceDocumentList.append(item);
        });
    }

    function setPanelFilter(panel) {
        activePanel = panel;
        filterButtons.forEach((button) => {
            const isActive = button.dataset.panelFilter === panel;
            button.classList.toggle("active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        });
        renderSystems();
    }

    filterButtons.forEach((button) => {
        button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
        button.addEventListener("click", () => setPanelFilter(button.dataset.panelFilter));
    });

    timelineToggle.addEventListener("click", () => {
        allTimelineOpen = !allTimelineOpen;
        document.querySelectorAll(".timeline-item").forEach((item) => {
            item.classList.toggle("open", allTimelineOpen);
            const summary = item.querySelector(".timeline-summary");
            if (summary) {
                summary.setAttribute("aria-expanded", String(allTimelineOpen));
            }
        });
        timelineToggle.textContent = allTimelineOpen ? "Collapse all stages" : "Expand all stages";
    });

    fetch(DATA_URL)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Report data returned HTTP ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            reportData = data;
            renderSystems();
            renderTimeline();
            renderSourceDocuments();
        })
        .catch((error) => {
            systemGrid.replaceChildren(element("p", "error-copy", "System profiles could not be loaded."));
            timeline.replaceChildren(element("p", "error-copy", "The evidence ledger could not be loaded."));
            sourceDocumentList.replaceChildren(element("li", "", "Document hashes could not be loaded."));
            console.error(error);
        });
})();
