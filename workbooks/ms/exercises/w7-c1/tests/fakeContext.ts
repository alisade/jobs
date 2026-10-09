/* Minimal fake of ComponentFramework.Context for unit tests. Only what the control reads. */
import { IInputs } from "../AssetTagInput/generated/ManifestTypes";

export interface FakeOptions {
    value?: string | null;
    prefix?: string | null;
    debounceMs?: number | null;
    disabled?: boolean;
    editable?: boolean;
}

export function fakeContext(o: FakeOptions = {}): ComponentFramework.Context<IInputs> {
    const ctx = {
        parameters: {
            assetTag: {
                raw: o.value === undefined ? null : o.value,
                formatted: o.value ?? "",
                error: false,
                errorMessage: "",
                type: "SingleLine.Text",
                security: o.editable === undefined ? undefined : { editable: o.editable, readable: true, secured: true },
            },
            tagPrefix: { raw: o.prefix === undefined ? "TSP" : o.prefix, error: false, errorMessage: "", type: "SingleLine.Text" },
            debounceMs: { raw: o.debounceMs === undefined ? 300 : o.debounceMs, error: false, errorMessage: "", type: "Whole.None" },
        },
        mode: { isControlDisabled: !!o.disabled, isVisible: true, label: "Asset tag" },
    };
    return ctx as unknown as ComponentFramework.Context<IInputs>;
}

export function type(input: HTMLInputElement, text: string): void {
    input.value = text;
    input.dispatchEvent(new Event("input", { bubbles: true }));
}

export function blur(input: HTMLInputElement): void {
    input.dispatchEvent(new Event("blur"));
}
