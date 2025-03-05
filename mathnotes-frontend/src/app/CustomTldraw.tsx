"use client";
import { useEffect } from "react";
import {
	Editor,
	Tldraw,
	track,
	useEditor,
	createShapeId,
	Geometry2d,
	HTMLContainer,
	RecordProps,
	Rectangle2d,
	ShapeUtil,
	T,
	TLBaseShape,
	DefaultFontStyle,
	DefaultFontFamilies,
} from "tldraw";
import "tldraw/tldraw.css";
import { blobToBase64 } from "./utils";
// adapted from https://tldraw.dev/examples/ui/custom-ui

DefaultFontStyle.setDefaultValue("draw");
type ICustomShape = TLBaseShape<
	"my-custom-shape",
	{
		w: number;
		h: number;
		text: string;
	}
>;
const LIGHT_FILL = "#adadad";
const DARK_FILL = "#ffcccc";
export class MyShapeUtil extends ShapeUtil<ICustomShape> {
	static override type = "my-custom-shape" as const;
	static override props: RecordProps<ICustomShape> = {
		w: T.number,
		h: T.number,
		text: T.string,
	};

	getDefaultProps(): ICustomShape["props"] {
		return {
			w: 500,
			h: 200,
			text: "",
		};
	}
	indicator(shape: ICustomShape) {
		return this.getSvgRect(shape);
	}
	getSvgRect(shape: ICustomShape, props?: { fill: string }) {
		return <rect width={shape.props.w} height={shape.props.h} {...props} />;
	}

	override canEdit() {
		return false;
	}
	override canResize() {
		return false;
	}
	override isAspectRatioLocked() {
		return false;
	}

	getGeometry(shape: ICustomShape): Geometry2d {
		return new Rectangle2d({
			width: shape.props.w,
			height: shape.props.h,
			isFilled: true,
		});
	}

	component(shape: ICustomShape) {
		const isDarkmode = this.editor.user.getIsDarkMode();
		return (
			<HTMLContainer
				id={shape.id}
				style={{ backgroundColor: isDarkmode ? DARK_FILL : LIGHT_FILL }}
				data-size='xl'
				className='result-box'
			>
				<pre
					className='text-xl'
					style={{ fontFamily: DefaultFontFamilies["draw"] }}
				>
					{shape["props"].text}
				</pre>
			</HTMLContainer>
		);
	}

	// [3]

	// function getFontDef(shape: ICustomShape): SvgExportDef {
	// 	//
	// 	return {
	// 		// some unique key,
	// 		key: 'my-custom-shape-font',
	// 		getElement: async () => {
	// 			return <style></style> element
	// 			check out the defaultStyleDefs.tsx file for an example of how
	// 			we do this for tldraw fonts
	// 		},
	// 	}
}

const customShape = [MyShapeUtil];
const results_id = createShapeId("Result-box");
export default function CustomTldraw() {
	return (
		<div className='tldraw__editor'>
			<Tldraw
				hideUi
				shapeUtils={customShape}
				onMount={(editor) => {
					editor.createShape({
						id: results_id,
						type: "my-custom-shape",
						x: 100,
						y: 100,
						props: { text: "" },
					});
				}}
			>
				<CustomUi />
			</Tldraw>
		</div>
	);
}

const CustomUi = track(() => {
	const editor = useEditor();
	useEffect(() => {
		const handleKeyUp = (e: KeyboardEvent) => {
			switch (e.key) {
				case "Delete":
				case "Backspace": {
					editor.deleteShapes(editor.getSelectedShapeIds());
					break;
				}
				case "v": {
					editor.setCurrentTool("select");
					break;
				}
				case "e": {
					editor.setCurrentTool("eraser");
					break;
				}
				case "x":
				case "p":
				case "b":
				case "d": {
					editor.setCurrentTool("draw");
					break;
				}
			}
		};

		window.addEventListener("keyup", handleKeyUp);
		return () => {
			window.removeEventListener("keyup", handleKeyUp);
		};
	});

	const handleSolve = async (editor: Editor) => {
		const shapeIds = editor.getCurrentPageShapeIds();
		// remove the result box from the input image
		shapeIds.delete(results_id);
		if (shapeIds.size === 0) return alert("No shapes on the canvas");

		try {
			const { blob } = await editor.toImage([...shapeIds], {
				format: "png",
				background: false,
			});

			// Convert blob to base64 string
			const base64Image = await blobToBase64(blob);
			// Remove the "data:image/png;base64," prefix if present
			if (!base64Image) {
				console.error("Failed to convert image to base64");
				return null;
			}
			const base64Data = base64Image.split(",")[1] || base64Image;

			console.log("Sending image data...");

			// Make sure Content-Type is properly set
			const response = await fetch("/api/calculate", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Accept: "application/json",
				},
				body: JSON.stringify({ image: base64Data }),
			});

			if (!response.ok) {
				const errorText = await response.text();
				console.error(
					`Server error (${response.status}): ${errorText}`
				);
				throw new Error(`Server error: ${response.status}`);
			}

			// Parse the JSON response
			const data = await response.json();
			let text = "";

			// Handle different operation types
			if (data && data.length > 0) {
				const result = data[0];
				console.log(data)
				switch (result.type) {
					case "equation":
						text = `Equation: ${
							result.latex
						}\n\nVariables: ${result.variables.join(
							", "
						)}\n\nSolutions:\n`;
						Object.entries(result.solutions).forEach(
							([variable, solution]) => {
								text += `${variable}: ${solution}\n`;
							}
						);
						break;

					case "integration":
						text = `Integration of: ${
							result.latex
						}\n\nVariables: ${result.variables.join(
							", "
						)}\n\nResults:\n`;
						Object.entries(result.results).forEach(
							([variable, solution]) => {
								text += `∫ w.r.t ${variable}: ${solution}\n`;
							}
						);
						break;

					case "differentiation":
						text = `Differentiation of: ${
							result.latex
						}\n\nVariables: ${result.variables.join(
							", "
						)}\n\nResults:\n`;
						Object.entries(result.results).forEach(
							([variable, solution]) => {
								text += `d/d${variable}: ${solution}\n`;
							}
						);
						break;

					case "expression":
						text = `Original Expression: ${result.original}\n\nSimplified: ${result.simplified}`;
						break;

					case "equation_without_variables":
						text = `Equation: ${result.latex}\n\nExpression: ${result.expression}\n\nResult: ${result.result}`;
						break;

					default:
						// Fallback for any error or unhandled type
						text = `Operation Type: ${result.type}\n\nLaTeX: ${
							result.latex
						}\n\nError: ${result.message || "Unknown error"}`;
				}
			} else {
				text = "No results found or invalid response";
			}

			editor.updateShapes([
				{
					id: results_id, // required
					type: "my-custom-shape", // required
					props: {
						text,
					},
				},
			]);

			return data;
		} catch (e) {
			console.error("Error in handleSolve:", e);
			return null;
		}
	};

	return (
		<div className='custom-layout'>
			<div className='custom-toolbar'>
				<button
					className='custom-button'
					data-isactive={editor.getCurrentToolId() === "select"}
					onClick={() => editor.setCurrentTool("select")}
				>
					Select
				</button>
				<button
					className='custom-button'
					data-isactive={editor.getCurrentToolId() === "draw"}
					onClick={() => editor.setCurrentTool("draw")}
				>
					Pencil
				</button>
				<button
					className='custom-button'
					data-isactive={editor.getCurrentToolId() === "eraser"}
					onClick={() => editor.setCurrentTool("eraser")}
				>
					Eraser
				</button>
				<button
					className='custom-button'
					onClick={() => handleSolve(editor)}
				>
					Solve
				</button>
			</div>
		</div>
	);
});
