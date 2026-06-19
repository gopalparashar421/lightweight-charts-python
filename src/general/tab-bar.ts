import { GlobalParams } from "./global-params";
import { Handler } from "./handler";

declare const window: GlobalParams;

interface TabEntry {
    handler: Handler;
    tabEl: HTMLButtonElement;
}

/**
 * SubChartManager — page-level singleton that manages a tab bar and controls
 * which Handler wrapper is visible at any one time.
 *
 * Created from Python via:
 *   window.mgrid = new Lib.SubChartManager()
 *
 * Handlers are registered via:
 *   window.mgrid.register('window.handlerId', 'Label', window.handlerId)
 */
export class SubChartManager {
    private _tabBar: HTMLDivElement;
    private _tabs: Map<string, TabEntry> = new Map();
    private _activeId: string = "";

    constructor() {
        this._tabBar = document.createElement("div");
        this._tabBar.classList.add("subchart-tab-bar");
        // prepend so the tab bar appears above all .handler wrappers
        window.containerDiv.prepend(this._tabBar);
    }

    /**
     * Register a Handler with the manager. The first registration becomes
     * the active (visible) tab; subsequent registrations are hidden until
     * the user selects them.
     */
    register(handlerId: string, label: string, handler: Handler): void {
        const tabEl = document.createElement("button");
        tabEl.classList.add("subchart-tab");
        tabEl.textContent = label;
        tabEl.addEventListener("click", () => this.showTab(handlerId));
        this._tabBar.appendChild(tabEl);
        this._tabs.set(handlerId, { handler, tabEl });

        if (this._tabs.size === 1) {
            // First registration — keep it active and visible
            tabEl.classList.add("subchart-tab-active");
            this._activeId = handlerId;
            handler.reSize();
        } else {
            // Subsequent registrations — hide until selected
            handler.wrapper.style.display = "none";
            // Tab bar height changed; resize the visible handler.
            const active = this._tabs.get(this._activeId);
            active?.handler.reSize();
        }
    }

    /**
     * Show the tab identified by *handlerId*, hiding all others. Calls
     * handler.reSize() on the newly visible handler to fix pixel dimensions.
     */
    showTab(handlerId: string): void {
        // Hide all wrappers and deactivate all tab buttons
        this._tabs.forEach(({ handler, tabEl }) => {
            handler.wrapper.style.display = "none";
            tabEl.classList.remove("subchart-tab-active");
        });

        const entry = this._tabs.get(handlerId);
        if (!entry) return;

        entry.handler.wrapper.style.display = "flex";
        entry.tabEl.classList.add("subchart-tab-active");
        this._activeId = handlerId;
        // Trigger resize so the chart fills the now-visible wrapper correctly
        entry.handler.reSize();
    }

    /**
     * Update the displayed label for a registered tab (for rename support).
     */
    updateLabel(handlerId: string, label: string): void {
        const entry = this._tabs.get(handlerId);
        if (entry) {
            entry.tabEl.textContent = label;
        }
    }

    /** Returns the handler ID of the currently visible tab. */
    get activeId(): string {
        return this._activeId;
    }
}
