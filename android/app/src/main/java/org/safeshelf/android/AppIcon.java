package org.safeshelf.android;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;

/** Small line icons with a shared stroke, independent of the device's emoji font. */
final class AppIcon extends View {
    private final String name;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    AppIcon(Context context, String name, int color) {
        super(context); this.name = name; paint.setColor(color); paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(1.65f); paint.setStrokeCap(Paint.Cap.ROUND); paint.setStrokeJoin(Paint.Join.ROUND);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    private void line(Canvas c, float... xy) {
        Path p = new Path(); p.moveTo(xy[0],xy[1]);
        for(int i=2;i<xy.length;i+=2) p.lineTo(xy[i],xy[i+1]); c.drawPath(p,paint);
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas); canvas.save();
        float width=getWidth()-getPaddingLeft()-getPaddingRight();
        float height=getHeight()-getPaddingTop()-getPaddingBottom();
        float size=Math.min(width,height);
        canvas.translate(getPaddingLeft()+(width-size)/2,getPaddingTop()+(height-size)/2); canvas.scale(size/24,size/24);
        switch(name) {
            case "Home": line(canvas,3,10,12,3,21,10); line(canvas,5,9,5,21,10,21,10,15,14,15,14,21,19,21,19,9); break;
            case "Eddy": canvas.drawRoundRect(3,4,21,18,4,4,paint); line(canvas,6,18,6,22,11,18); line(canvas,8,10,8.1f,10); line(canvas,12,10,12.1f,10); line(canvas,16,10,16.1f,10); break;
            case "My Shelf": line(canvas,3,21,3,4); line(canvas,21,21,21,4); line(canvas,3,12,21,12); line(canvas,3,21,21,21); canvas.drawRect(6,5,10,12,paint); canvas.drawRect(13,3,18,12,paint); canvas.drawRect(7,16,17,21,paint); break;
            case "Account": canvas.drawCircle(12,8,4,paint); canvas.drawArc(4,14,20,28,180,180,false,paint); break;
            case "scan": line(canvas,3,8,3,3,8,3); line(canvas,16,3,21,3,21,8); line(canvas,3,16,3,21,8,21); line(canvas,16,21,21,21,21,16); line(canvas,7,9,17,9); line(canvas,7,12,17,12); line(canvas,7,15,13,15); break;
            case "voice": canvas.drawRoundRect(9,3,15,15,3,3,paint); canvas.drawArc(6,7,18,19,0,180,false,paint); line(canvas,12,19,12,22); line(canvas,9,22,15,22); break;
            case "link": canvas.save(); canvas.rotate(-40,12,12); canvas.drawRoundRect(3,8,14,16,4,4,paint); canvas.drawRoundRect(10,8,21,16,4,4,paint); canvas.restore(); break;
            case "arrow": line(canvas,6,18,18,6); line(canvas,6,6,18,6,18,18); break;
            case "shield": line(canvas,12,2,21,6,20,15,17,19,12,22,7,19,4,15,3,6,12,2); line(canvas,8,12,11,15,17,9); break;
            default: canvas.drawCircle(12,12,9,paint); line(canvas,12,7,12,13); line(canvas,12,17,12.1f,17);
        }
        canvas.restore();
    }
}
