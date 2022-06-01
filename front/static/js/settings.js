$('#inputImageFile').on('change', function (e) {
    let output = $('#filePreview')
    let url = URL.createObjectURL(e.target.files[0])
    output.attr('src', url)
    output.on('load', function () {
        URL.revokeObjectURL(url)
    })
})
