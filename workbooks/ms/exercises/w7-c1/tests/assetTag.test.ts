import { AssetTagInput } from "../AssetTagInput/index";
import { fakeContext, type, blur } from "./fakeContext";

function mount(value: string | null = null) {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const notify = jest.fn();
    const control = new AssetTagInput();
    const ctx = fakeContext({ value });
    control.init(ctx, notify, {}, container);
    control.updateView(ctx);
    const input = container.querySelector("input") as HTMLInputElement;
    return { container, notify, control, input };
}

describe("AssetTagInput (visible tests)", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => { jest.useRealTimers(); document.body.innerHTML = ""; });

    test("renders the bound value on load", () => {
        const { input } = mount("TSP-004211");
        expect(input.value).toBe("TSP-004211");
    });

    test("a valid tag typed by the user is committed once after the debounce", () => {
        const { input, notify, control } = mount(null);
        type(input, "TSP-123456");
        expect(notify).not.toHaveBeenCalled();
        jest.advanceTimersByTime(300);
        expect(notify).toHaveBeenCalledTimes(1);
        expect(control.getOutputs().assetTag).toBe("TSP-123456");
    });

    test("lower case and missing dash are normalized", () => {
        const { input, notify, control } = mount(null);
        type(input, " tsp123456 ");
        blur(input);
        expect(notify).toHaveBeenCalledTimes(1);
        expect(control.getOutputs().assetTag).toBe("TSP-123456");
    });

    test("an invalid tag is not committed and shows an error", () => {
        const { input, notify, container } = mount(null);
        type(input, "TSP-12");
        blur(input);
        expect(notify).not.toHaveBeenCalled();
        const err = container.querySelector(".tsp-error") as HTMLElement;
        expect(err).not.toBeNull();
        expect(err.hidden).toBe(false);
    });
});
