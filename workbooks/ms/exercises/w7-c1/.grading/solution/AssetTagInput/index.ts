import { IInputs, IOutputs } from "./generated/ManifestTypes";

const DEFAULT_PREFIX = "TSP";
const DEFAULT_DEBOUNCE_MS = 400;

/**
 * Tailspin asset tag input (reference solution).
 * Commits a value to the bound column only when it is a valid, normalized tag that differs
 * from the last known value. Platform-driven updates (updateView) never echo back.
 */
export class AssetTagInput implements ComponentFramework.StandardControl<IInputs, IOutputs> {
    private notifyOutputChanged!: () => void;
    private root!: HTMLDivElement;
    private input!: HTMLInputElement;
    private error!: HTMLDivElement;
    private lastValue: string | undefined = undefined;
    private prefix = DEFAULT_PREFIX;
    private debounceMs = DEFAULT_DEBOUNCE_MS;
    private timer: ReturnType<typeof setTimeout> | undefined = undefined;
    private readonly onInput = (): void => this.scheduleCommit();
    private readonly onBlur = (): void => this.commitNow();

    public init(
        context: ComponentFramework.Context<IInputs>,
        notifyOutputChanged: () => void,
        _state: ComponentFramework.Dictionary,
        container: HTMLDivElement
    ): void {
        this.notifyOutputChanged = notifyOutputChanged;
        this.root = document.createElement("div");
        this.root.className = "tsp-assettag";
        this.input = document.createElement("input");
        this.input.type = "text";
        this.input.setAttribute("aria-label", "Asset tag");
        this.error = document.createElement("div");
        this.error.className = "tsp-error";
        this.error.setAttribute("role", "alert");
        this.error.hidden = true;
        this.root.appendChild(this.input);
        this.root.appendChild(this.error);
        container.appendChild(this.root);
        this.input.addEventListener("input", this.onInput);
        this.input.addEventListener("blur", this.onBlur);
        this.applyContext(context);
    }

    public updateView(context: ComponentFramework.Context<IInputs>): void {
        this.applyContext(context);
    }

    public getOutputs(): IOutputs {
        return { assetTag: this.lastValue };
    }

    public destroy(): void {
        this.clearTimer();
        if (this.input) {
            this.input.removeEventListener("input", this.onInput);
            this.input.removeEventListener("blur", this.onBlur);
        }
        if (this.root && this.root.parentElement) {
            this.root.parentElement.removeChild(this.root);
        }
    }

    // --- helpers -------------------------------------------------------------

    private applyContext(context: ComponentFramework.Context<IInputs>): void {
        const p = context.parameters.tagPrefix?.raw;
        this.prefix = p && p.trim() ? p.trim().toUpperCase() : DEFAULT_PREFIX;
        const d = context.parameters.debounceMs?.raw;
        this.debounceMs = typeof d === "number" && d >= 0 ? d : DEFAULT_DEBOUNCE_MS;

        const security = context.parameters.assetTag.security;
        this.input.disabled = context.mode.isControlDisabled || (security !== undefined && security.editable === false);

        const raw = context.parameters.assetTag.raw;
        const incoming = raw === null || raw === undefined || raw === "" ? undefined : raw;
        if (incoming !== this.lastValue) {
            // The platform changed the value (load, another script, a save round-trip).
            this.lastValue = incoming;
            if (this.timer === undefined) {
                this.input.value = incoming ?? "";
                this.showError(false);
            }
        }
    }

    private normalize(text: string): string {
        const s = text.replace(/\s+/g, "").toUpperCase();
        const glued = new RegExp("^" + this.escape(this.prefix) + "(\\d{6})$");
        const m = glued.exec(s);
        return m ? this.prefix + "-" + m[1] : s;
    }

    private isValid(tag: string): boolean {
        return new RegExp("^" + this.escape(this.prefix) + "-\\d{6}$").test(tag);
    }

    private escape(s: string): string {
        return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    private scheduleCommit(): void {
        this.clearTimer();
        this.timer = setTimeout(() => {
            this.timer = undefined;
            this.commit();
        }, this.debounceMs);
    }

    private commitNow(): void {
        if (this.timer === undefined) {
            // Nothing typed since the last commit; still validate what is shown.
            this.commit();
            return;
        }
        this.clearTimer();
        this.commit();
    }

    private clearTimer(): void {
        if (this.timer !== undefined) {
            clearTimeout(this.timer);
            this.timer = undefined;
        }
    }

    private commit(): void {
        const text = this.input.value;
        if (text.trim() === "") {
            this.showError(false);
            this.setValue(undefined);
            return;
        }
        const tag = this.normalize(text);
        if (!this.isValid(tag)) {
            this.showError(true);
            return;
        }
        this.showError(false);
        this.input.value = tag;
        this.setValue(tag);
    }

    private setValue(value: string | undefined): void {
        if (value === this.lastValue) {
            return;
        }
        this.lastValue = value;
        this.notifyOutputChanged();
    }

    private showError(on: boolean): void {
        this.root.classList.toggle("tsp-invalid", on);
        this.error.hidden = !on;
        this.error.textContent = on ? "Expected format " + this.prefix + "-123456" : "";
    }
}
