import * as fs from "fs";
import * as path from "path";
import { AssetTagInput } from "../../AssetTagInput/index";
import { fakeContext, typeText, blur, FakeOptions } from "./hiddenContext";

const ROOT = path.resolve(__dirname, "..", "..");

function mount(opts: FakeOptions = {}) {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const notify = jest.fn();
    const control = new AssetTagInput();
    const ctx = fakeContext(opts);
    control.init(ctx, notify, {}, container);
    control.updateView(ctx);
    const input = container.querySelector("input") as HTMLInputElement;
    return { container, notify, control, input };
}

describe("lifecycle and platform updates", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => { jest.useRealTimers(); document.body.innerHTML = ""; });

    test("init and updateView never call notifyOutputChanged", () => {
        const { notify } = mount({ value: "TSP-000001" });
        jest.advanceTimersByTime(5000);
        expect(notify).not.toHaveBeenCalled();
    });

    test("platform-driven value change in updateView does not echo back", () => {
        const { control, notify, input } = mount({ value: "TSP-000001" });
        control.updateView(fakeContext({ value: "TSP-999999" }));
        jest.advanceTimersByTime(5000);
        expect(input.value).toBe("TSP-999999");
        expect(notify).not.toHaveBeenCalled();
        expect(control.getOutputs().assetTag).toBe("TSP-999999");
    });

    test("null raw value renders empty and outputs undefined", () => {
        const { input, control } = mount({ value: null });
        expect(input.value).toBe("");
        expect(control.getOutputs().assetTag).toBeUndefined();
    });

    test("typing the value already stored does not notify", () => {
        const { input, notify } = mount({ value: "TSP-123456" });
        typeText(input, "tsp 123456");
        blur(input);
        jest.advanceTimersByTime(1000);
        expect(notify).not.toHaveBeenCalled();
    });

    test("rapid keystrokes are debounced into a single notification", () => {
        const { input, notify, control } = mount({ value: null });
        for (const partial of ["T", "TS", "TSP-1", "TSP-1234", "TSP-123456"]) {
            typeText(input, partial);
            jest.advanceTimersByTime(100);
        }
        expect(notify).not.toHaveBeenCalled();
        jest.advanceTimersByTime(300);
        expect(notify).toHaveBeenCalledTimes(1);
        expect(control.getOutputs().assetTag).toBe("TSP-123456");
    });

    test("blur commits immediately and cancels the pending debounce", () => {
        const { input, notify } = mount({ value: null });
        typeText(input, "TSP-222222");
        blur(input);
        expect(notify).toHaveBeenCalledTimes(1);
        jest.advanceTimersByTime(2000);
        expect(notify).toHaveBeenCalledTimes(1);
    });

    test("debounceMs input property is honoured", () => {
        const { input, notify } = mount({ value: null, debounceMs: 1000 });
        typeText(input, "TSP-333333");
        jest.advanceTimersByTime(999);
        expect(notify).not.toHaveBeenCalled();
        jest.advanceTimersByTime(1);
        expect(notify).toHaveBeenCalledTimes(1);
    });

    test("missing debounceMs falls back to 400 ms", () => {
        const { input, notify } = mount({ value: null, debounceMs: null });
        typeText(input, "TSP-444444");
        jest.advanceTimersByTime(399);
        expect(notify).not.toHaveBeenCalled();
        jest.advanceTimersByTime(1);
        expect(notify).toHaveBeenCalledTimes(1);
    });
});

describe("validation and outputs", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => { jest.useRealTimers(); document.body.innerHTML = ""; });

    test("invalid text keeps the last valid output and marks the control invalid", () => {
        const { input, control, notify, container } = mount({ value: "TSP-000001" });
        typeText(input, "TSP-00");
        blur(input);
        expect(notify).not.toHaveBeenCalled();
        expect(control.getOutputs().assetTag).toBe("TSP-000001");
        expect(container.querySelector(".tsp-assettag")!.classList.contains("tsp-invalid")).toBe(true);
        const err = container.querySelector(".tsp-error") as HTMLElement;
        expect(err.getAttribute("role")).toBe("alert");
        expect(err.textContent).toContain("TSP-123456");
    });

    test("fixing an invalid value clears the error", () => {
        const { input, container } = mount({ value: null });
        typeText(input, "bad");
        blur(input);
        typeText(input, "TSP-555555");
        blur(input);
        const err = container.querySelector(".tsp-error") as HTMLElement;
        expect(err.hidden).toBe(true);
        expect(container.querySelector(".tsp-assettag")!.classList.contains("tsp-invalid")).toBe(false);
    });

    test("clearing the field outputs undefined and notifies once", () => {
        const { input, control, notify } = mount({ value: "TSP-000001" });
        typeText(input, "   ");
        blur(input);
        expect(notify).toHaveBeenCalledTimes(1);
        expect(control.getOutputs().assetTag).toBeUndefined();
    });

    test("custom tagPrefix is used for validation and normalization", () => {
        const { input, control } = mount({ value: null, prefix: "nwl" });
        typeText(input, "TSP-123456");
        blur(input);
        expect(control.getOutputs().assetTag).toBeUndefined();
        typeText(input, "nwl654321");
        blur(input);
        expect(control.getOutputs().assetTag).toBe("NWL-654321");
    });

    test("a prefix with regex metacharacters is matched literally", () => {
        const { input, control } = mount({ value: null, prefix: "A.B" });
        typeText(input, "AXB-123456");
        blur(input);
        expect(control.getOutputs().assetTag).toBeUndefined();
        typeText(input, "a.b-123456");
        blur(input);
        expect(control.getOutputs().assetTag).toBe("A.B-123456");
    });

    test("committed value is shown normalized in the input", () => {
        const { input } = mount({ value: null });
        typeText(input, "tsp 777777");
        blur(input);
        expect(input.value).toBe("TSP-777777");
    });
});

describe("disabled state", () => {
    afterEach(() => { document.body.innerHTML = ""; });

    test("isControlDisabled disables the input", () => {
        const { input } = mount({ value: "TSP-000001", disabled: true });
        expect(input.disabled).toBe(true);
    });

    test("field security editable=false disables the input", () => {
        const { input } = mount({ value: "TSP-000001", editable: false });
        expect(input.disabled).toBe(true);
    });

    test("re-enabled on a later updateView", () => {
        const { input, control } = mount({ value: "TSP-000001", disabled: true });
        control.updateView(fakeContext({ value: "TSP-000001", disabled: false }));
        expect(input.disabled).toBe(false);
    });
});

describe("destroy", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => { jest.useRealTimers(); document.body.innerHTML = ""; jest.restoreAllMocks(); });

    test("removes every listener it added", () => {
        const added: string[] = [];
        const removed: string[] = [];
        const addSpy = jest.spyOn(HTMLInputElement.prototype, "addEventListener").mockImplementation(function (this: HTMLInputElement, t: string, l: any, o?: any) {
            added.push(t);
            return EventTarget.prototype.addEventListener.call(this, t, l, o);
        });
        const remSpy = jest.spyOn(HTMLInputElement.prototype, "removeEventListener").mockImplementation(function (this: HTMLInputElement, t: string, l: any, o?: any) {
            removed.push(t);
            return EventTarget.prototype.removeEventListener.call(this, t, l, o);
        });
        const { control } = mount({ value: null });
        control.destroy();
        expect(added.length).toBeGreaterThan(0);
        expect(removed.sort()).toEqual(added.sort());
        addSpy.mockRestore();
        remSpy.mockRestore();
    });

    test("events after destroy do not notify", () => {
        const { input, notify, control } = mount({ value: null });
        control.destroy();
        typeText(input, "TSP-123456");
        blur(input);
        jest.advanceTimersByTime(2000);
        expect(notify).not.toHaveBeenCalled();
    });

    test("a pending debounce timer is cancelled by destroy", () => {
        const { input, notify, control } = mount({ value: null });
        typeText(input, "TSP-123456");
        control.destroy();
        jest.advanceTimersByTime(2000);
        expect(notify).not.toHaveBeenCalled();
    });

    test("removes its DOM from the container", () => {
        const { container, control } = mount({ value: null });
        control.destroy();
        expect(container.querySelector("input")).toBeNull();
    });
});

describe("ControlManifest.Input.xml", () => {
    const xml = fs.readFileSync(path.join(ROOT, "AssetTagInput", "ControlManifest.Input.xml"), "utf8");
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    const control = doc.querySelector("manifest > control");
    const prop = (name: string) => doc.querySelector(`control > property[name="${name}"]`);

    test("is well-formed with a standard control", () => {
        expect(doc.getElementsByTagName("parsererror").length).toBe(0);
        expect(control).not.toBeNull();
        expect(control!.getAttribute("constructor")).toBe("AssetTagInput");
        expect(control!.getAttribute("namespace")).toBeTruthy();
        expect(control!.getAttribute("control-type")).toBe("standard");
        expect(control!.getAttribute("version")).toMatch(/^\d+\.\d+\.\d+$/);
    });

    test("assetTag is a bound SingleLine.Text property", () => {
        const p = prop("assetTag");
        expect(p).not.toBeNull();
        expect(p!.getAttribute("usage")).toBe("bound");
        expect(p!.getAttribute("of-type")).toBe("SingleLine.Text");
    });

    test("tagPrefix and debounceMs are input properties of the right types", () => {
        const a = prop("tagPrefix");
        const b = prop("debounceMs");
        expect(a).not.toBeNull();
        expect(b).not.toBeNull();
        expect(a!.getAttribute("usage")).toBe("input");
        expect(a!.getAttribute("of-type")).toBe("SingleLine.Text");
        expect(b!.getAttribute("usage")).toBe("input");
        expect(b!.getAttribute("of-type")).toBe("Whole.None");
    });

    test("every property in ManifestTypes.d.ts is declared in the manifest", () => {
        const dts = fs.readFileSync(path.join(ROOT, "AssetTagInput", "generated", "ManifestTypes.d.ts"), "utf8");
        const block = dts.split("interface IInputs")[1].split("}")[0];
        const names = Array.from(block.matchAll(/(\w+)\s*:/g)).map((m: RegExpMatchArray) => m[1]);
        expect(names.length).toBeGreaterThan(0);
        for (const n of names) {
            expect(prop(n)).not.toBeNull();
        }
    });

    test("code and css resources are registered and exist on disk", () => {
        const code = doc.querySelector("resources > code");
        const css = doc.querySelector("resources > css");
        expect(code).not.toBeNull();
        expect(code!.getAttribute("path")).toBe("index.ts");
        expect(css).not.toBeNull();
        const cssPath = css!.getAttribute("path")!;
        expect(fs.existsSync(path.join(ROOT, "AssetTagInput", cssPath))).toBe(true);
    });
});
