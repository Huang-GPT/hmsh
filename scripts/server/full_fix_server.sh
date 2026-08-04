# 涓€娆℃€у畬鏁磋瘖鏂?淇+楠岃瘉锛堟湇鍔″櫒 VNC 缁堢璺戯級
# 浣犲鍒剁矘璐村埌鏈嶅姟鍣?VNC 缁堢锛?*鍙窇涓€娆?*

set -e
cd /hongmen-after-sales
export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_hmsh -o IdentitiesOnly=yes"

echo "============================================"
echo "[STEP 1] git pull origin master"
echo "============================================"
git pull origin master --no-edit 2>&1

echo ""
echo "============================================"
echo "[STEP 2] 楠岃瘉婧愮爜宸叉洿鏂?
echo "============================================"
echo "AdminOrders.vue 鏂?CSS class 璁℃暟锛堝簲 >= 3锛?"
grep -c "cv-empty\|dot-cyan\|appt-hint" frontend/src/views/admin/AdminOrders.vue

echo ""
echo "git log 鏈€鏂?3 涓?commit:"
git log --oneline -3

echo ""
echo "============================================"
echo "[STEP 3] 閲嶅缓鍓嶇 Docker 闀滃儚"
echo "============================================"
docker compose stop frontend 2>&1
docker compose rm -f frontend 2>&1
docker rmi hongmen-frontend:latest 2>/dev/null
docker compose build --no-cache --pull frontend 2>&1 | tail -5
docker compose up -d --force-recreate frontend 2>&1
sleep 8

echo ""
echo "============================================"
echo "[STEP 4] 楠岃瘉 dist 宸叉洿鏂?
echo "============================================"
echo "dist js 鏂囦欢:"
docker exec hongmen-frontend ls /usr/share/nginx/html/js/

echo ""
echo "dist 涓柊 CSS class 璁℃暟锛堝簲 cv-empty>=7, dot-cyan>=1, appt-hint>=1锛?"
docker exec hongmen-frontend sh -c "grep -o 'cv-empty\|dot-cyan\|appt-hint' /usr/share/nginx/html/js/app.*.js | sort | uniq -c"

echo ""
echo "============================================"
echo "瀹屾垚銆傚鍒朵互涓婅緭鍑鸿创缁?agent銆?
echo "============================================"
