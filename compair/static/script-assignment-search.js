let api_url = "/api/assignment/search/enddate";

function getObject(object)
{
    strURL = api_url.concat('?compare_end=').concat(object.value);
    getsearchapi(strURL);
}

// Defining async function
async function getsearchapi(url) {

    // Storing response
    const response = await fetch(url);

    // Storing data in form of JSON
    var search_data = await response.json();
    //console.log(search_data);
    if (response) {
        hideloadersearch();
    }
    showsearchapi(search_data);
}
// Calling that async function
//getapi(api_url);

// Function to hide the loader
function hideloadersearch() {
    document.getElementById('loading').style.display = 'none';
}
// Function to define innerHTML for HTML table
function showsearchapi(search_data) {

    //const myObj = JSON.parse(data);

    let tab = `<tr>
          <th>Uuid</th>
          <th>Name</th>
          <th>Compare_Start</th>
          <th>Compare_End</th>
         </tr>`;


    for (let key in  search_data) {
        //tab += `<tr><td colspan="4">${search_data[key]}</td></tr>`;
        let obj = JSON.parse(search_data[key])
        tab += `<tr><td>${JSON.stringify(obj.uuid).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.name).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_start).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_end).replace(/\"/g, "")}</td></tr>`;
    }

    // Setting innerHTML as tab variable
    document.getElementById("apiresults").innerHTML = tab;
}

getsearchapi(api_url);
