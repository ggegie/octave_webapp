const myOptions = [
    { label: 'ดีใจ', value: 'happy' },
    { label: 'สนุกสนาน', value: 'fun' },
    { label: 'ร่าเริง', value: 'cheerful' },
    { label: 'รัก', value: 'love' },
    { label: 'เครียด', value: 'stressed' },
    { label: 'โกรธ', value: 'angry' }
];

VirtualSelect.init({
    ele: '#emotion-select',
    options: myOptions,
    multiple: true,
    maxValues: 3, // Limit the number of selections to 3
    search: true, // Enable the live search feature
    placeholder: 'Select emotions',
    noOptionsText: 'No emotions found',
    noSearchResultsText: 'No results found',
    hideClearButton: false, // Show the clear button to allow users to easily reset their selection
    // Optional: add more configurations as needed from the documentation
});

document.querySelector('#emotion-select').addEventListener('change', function() {
    console.log(this.value); // Here you can handle the logic based on selected values
});
  
  

  






// const selectBtn = document.querySelector(".select-btn"),
//       items = document.querySelectorAll(".item");
// selectBtn.addEventListener("click", () => {
//     selectBtn.classList.toggle("open");
// });
// items.forEach(item => {
//     item.addEventListener("click", () => {
//         item.classList.toggle("checked");
//         let checked = document.querySelectorAll(".checked"),
//             btnText = document.querySelector(".btn-text");
//             if(checked && checked.length > 0){
//                 btnText.innerText = `${checked.length} Selected`;
//             }else{
//                 btnText.innerText = "Select Language";
//             }
//     });
// })

