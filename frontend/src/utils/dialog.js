/**
 * Vant 2 弹窗「提交失败不关闭」统一封装
 *
 * 背景（Vant 2 的真实行为，源码 node_modules/vant/lib/dialog/Dialog.js）：
 *
 *   handleAction(action) {
 *     this.$emit(action);                        // ← @confirm 的返回值被丢弃
 *     if (!this.value) return;
 *     if (this.beforeClose) {
 *       this.loading[action] = true;
 *       this.beforeClose(action, function (state) {
 *         if (state !== false && this.loading[action]) this.onClose(action);  // ← done(false) 才拦住
 *         ...
 *       });
 *     } else {
 *       this.onClose(action);                    // ← 没有 beforeClose 就无条件关闭
 *     }
 *   }
 *
 * 结论：Vant 2 的 van-dialog **不支持**在 `@confirm` 处理器里 `return false`
 *       来阻止关闭（那是 Vant 3 的行为）。只有 `before-close` 属性可以拦住。
 *
 * 用法：
 *   模板:  <van-dialog v-model="showForm" :before-close="bcForm" @confirm="..." />
 *   脚本:  created() { this.bcForm = makeBeforeClose(this.submitForm) }
 *
 *   submitForm() 约定：成功返回 truthy / 失败返回 false 或抛异常
 *   - 失败 → done(false) → 弹窗保持打开，用户填的内容不丢
 *   - 成功 → done()    → 弹窗关闭
 */

/**
 * 生成 Vant 2 before-close 处理器
 * @param {Function} submitFn  提交逻辑，返回 Promise<boolean|any>；falsy/抛错视为失败
 * @returns {Function} (action: 'confirm'|'cancel', done: Function) => void
 */
export function makeBeforeClose(submitFn) {
  return function beforeCloseHandler(action, done) {
    // 取消：直接关闭
    if (action !== 'confirm') {
      done()
      return
    }
    let ret
    try {
      ret = submitFn.call(this)
    } catch (e) {
      // 同步异常也视为失败，保持弹窗打开
      done(false)
      return
    }
    Promise.resolve(ret)
      .then((ok) => {
        // 返回 false 明确表示失败；其他 truthy / undefined 视为成功
        done(ok === false ? false : true)
      })
      .catch(() => {
        done(false)
      })
  }
}

/**
 * 把一组 [name -> submitFn] 挂到组件实例上，供模板 :before-close="xxx" 使用
 * @param {Object} vm     Vue 组件实例
 * @param {Object} map    { bcForm: submitFn, bcAssign: submitFn2 }
 */
export function bindBeforeClosers(vm, map) {
  Object.keys(map).forEach((key) => {
    vm[key] = makeBeforeClose(map[key])
  })
}
