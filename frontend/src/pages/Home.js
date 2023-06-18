import React from "react";
import { useEffect, useState } from "react";

import axios from "axios";

const filingInfo = {
  "4": "News filing provides updates and announcements about the company.",
  "8-k":"Alert filing indicates important alerts or notifications related to the company.",
  "Update": "Update filing contains updates and changes related to the company.",
};


const fetchData = async () => {
  const response = await axios.get("http://127.0.0.1:8000/getLatestFilings/");
  const data = response.data;

  return data;
};


const Home = () => {
  const [jsonData, setJsonData] = useState([]);

  useEffect(() => {
    const getData = async () => {
      const data = await fetchData();

      // TODO

      setJsonData(data);
    };

    getData();
  }, []);

  return (
    <div className="table-container">
    <h1> Latest Filings </h1>
    <table className="table">
      <thead>
        <tr>
          <th>Filing Type</th>
          <th>Companies</th>
          <th>Tickers</th>
          <th>Time</th>
          <th>URL</th>
        </tr>
      </thead>
      <tbody>
        {Object.keys(jsonData).map((key) => {
          const item = jsonData[key];
          return (
            <tr key={key}>
              <td>{item.type}</td>
              <td>{JSON.parse(item.companies)}</td>
              <td>{item.tickers}</td>
              <td>{item.time}</td>
              <td>
                <a href={item.url} target="_blank">View Full Filing</a>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
    </div>
  );
};

export default Home;
