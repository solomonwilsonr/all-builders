import rasterio, numpy as np
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from PIL import Image
# Balram (ex-Kalinga) OCP bbox from the 2025 EC: 20°55'53.6"-20°59'7.11"N, 85°2'36.37"-85°6'21.71"E
bb=(85+2/60+36.37/3600, 20+55/60+53.6/3600, 85+6/60+21.71/3600, 20+59/60+7.11/3600)
base='https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/45/Q/TD/{y}/{m}/{id}/{b}.tif'
scenes={'2021-02-16 (pre-expiry)':('2021','2','S2A_45QTD_20210216_1_L2A'),
        '2023-02-11 (post-expiry)':('2023','2','S2B_45QTD_20230211_0_L2A'),
        '2025-02-10':('2025','2','S2B_45QTD_20250210_0_L2A')}
masks={}
for name,(y,m,i) in scenes.items():
    arr={}
    for b in ['B04','B08','TCI']:
        with rasterio.open(base.format(y=y,m=m,id=i,b=b)) as src:
            w=from_bounds(*transform_bounds('EPSG:4326',src.crs,*bb),src.transform)
            arr[b]=src.read(window=w)
    off=1000 if int(y)>=2022 else 0
    r,n=arr["B04"][0].astype(float)-off,arr["B08"][0].astype(float)-off
    ndvi=(n-r)/(n+r+1e-6)
    nonveg=ndvi<0.2
    masks[name]=nonveg
    px=nonveg.size
    print(f"{name}: window {nonveg.shape}, non-vegetated (NDVI<0.2) = {nonveg.mean()*100:.1f}% = {nonveg.sum()*0.01:.0f} ha of {px*0.01:.0f} ha bbox")
    Image.fromarray(np.moveaxis(arr['TCI'],0,-1)).save(f"balram_{y}.png")
k=list(masks)
for a,b in [(0,1),(1,2)]:
    A,B=masks[k[a]],masks[k[b]]
    h=min(A.shape[0],B.shape[0]); w=min(A.shape[1],B.shape[1]); A,B=A[:h,:w],B[:h,:w]
    print(f"{k[a]} -> {k[b]}: newly cleared {(B&~A).sum()*0.01:.0f} ha, revegetated {(A&~B).sum()*0.01:.0f} ha")
