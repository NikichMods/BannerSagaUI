// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;

    /** Neutral engineering renderer, deliberately not a proposed final design. */
    public final class PreviewLayer extends Sprite {
        private var labels:Array = [];

        public function PreviewLayer() {
            mouseEnabled = mouseChildren = false;
            visible = false;
        }

        public function show(frame:PreviewFrame, locate:Function):void {
            clear();
            if (!frame) return;
            for each (var row:Object in frame.rows) {
                var text:TextField = new TextField();
                text.mouseEnabled = false;
                text.selectable = false;
                text.autoSize = TextFieldAutoSize.LEFT;
                text.defaultTextFormat = new TextFormat("_sans", 14, 0xFFFFFF);
                text.background = true;
                text.backgroundColor = 0x202020;
                text.text = "ARM " + row.armor + "  STR " + row.strength;
                if (row.auraBefore != row.auraAfter) text.appendText("  SW " + row.auraAfter);
                labels.push({id:row.id, text:text});
                addChild(text);
            }
            updatePositions(locate);
        }

        public function updatePositions(locate:Function):void {
            var anyVisible:Boolean = false;
            for each (var label:Object in labels) {
                var point:Point = locate(label.id) as Point;
                label.text.visible = point != null;
                if (point) {
                    label.text.x = point.x;
                    label.text.y = point.y;
                    anyVisible = true;
                }
            }
            visible = anyVisible;
        }

        public function clear():void {
            while (numChildren) removeChildAt(numChildren - 1);
            labels = [];
            visible = false;
        }
    }
}
