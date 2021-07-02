function changeSlider() {
    let $amount = $("#amount")
    let $inputs = $("#inputs")
    $inputs.value = $amount.val()
    $amount.value = $inputs.val()

    console.log(`${$amount.val()}`)
    console.log(`${$inputs.val()}`)
}