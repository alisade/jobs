import { IInputs, IOutputs } from "./generated/ManifestTypes";

const DEFAULT_PREFIX = "TSP";
const DEFAULT_DEBOUNCE_MS = 400;

/**
 * Tailspin asset tag input. See README.md for the behaviour contract.
 *
 * Lifecycle reminder (PCF): init -> updateView -> (user edits -> notifyOutputChanged ->
 * getOutputs -> updateView)* -> destroy.
 */
export class AssetTagInput implements ComponentFramework.StandardControl<IInputs, IOutputs> {
    private notifyOutputChanged!: () => void;
    private container!: HTMLDivElement;
    private input!: HTMLInputElement;
    private lastValue: string | undefined = undefined;
    private prefix = DEFAULT_PREFIX;
    private debounceMs = DEFAULT_DEBOUNCE_MS;

    public init(
        context: ComponentFramework.Context<IInputs>,
        notifyOutputChanged: () => void,
        _state: ComponentFramework.Dictionary,
        container: HTMLDivElement
    ): void {
        this.notifyOutputChanged = notifyOutputChanged;
        this.container = container;
        this.input = document.createElement("input");
        this.input.type = "text";
        container.appendChild(this.input);

        // TODO: build the root element (class "tsp-assettag") holding the input and an error
        //       element (class "tsp-error", role="alert", hidden when the value is valid).
        // TODO: debounce "input" events by debounceMs; commit immediately on "blur".
        //       Keep references to your handlers so destroy() can remove them.
        // NOTE: this naive handler notifies on every keystroke, even for invalid text. Replace it.
        this.input.addEventListener("input", () => {
            this.lastValue = this.input.value;
            this.notifyOutputChanged();
        });
        void context;
        void this.prefix;
        void this.debounceMs;
    }

    public updateView(context: ComponentFramework.Context<IInputs>): void {
        // TODO: read tagPrefix / debounceMs (with defaults), apply disabled state
        //       (context.mode.isControlDisabled and field security), and reflect platform
        //       changes to assetTag.raw (null means empty) WITHOUT calling notifyOutputChanged.
        this.input.value = context.parameters.assetTag.raw ?? "";
    }

    public getOutputs(): IOutputs {
        // TODO: return only a valid, normalized tag, or undefined to clear the column.
        return { assetTag: this.lastValue };
    }

    public destroy(): void {
        // TODO: remove listeners, cancel any pending debounce timer, remove your DOM.
    }
}
