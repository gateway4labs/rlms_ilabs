using System;
using System.Collections.Generic;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Data;
using System.Data.SqlClient;
using System.Configuration;
using System.Xml;
using System.Web.UI.HtmlControls;
using System.IO;

public partial class clientList : System.Web.UI.Page
{
    string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];

    protected void Page_Load(object sender, EventArgs e)
    {
        string authKey = null;

        //Create an html form to be displayed in case POST param or GET auth header is not set

        if ((Request.Form["authKey"] == null) & (Request.Headers["X-ISA-Auth-Key"] == null))
        {
            Response.Write("This service returns a list of online lab clients for an specific authority. <br><br>");
            HtmlForm form = new HtmlForm();
            form.ID = "sendKeyForm";
            form.Method = "POST";
            form.InnerText = "authKey: ";

            HtmlInputText inputKey = new HtmlInputText();
            inputKey.ID = "authKey";

            HtmlInputSubmit Submitbutton = new HtmlInputSubmit();
            Submitbutton.Value = "Invoke";

            form.Controls.Add(inputKey);
            form.Controls.Add(Submitbutton);
            Page.Controls.Add(form);

        }
        else
        {
            if (Request.Headers["X-ISA-Auth-Key"] == null)
            {
                authKey = Request.Form["authKey"];
            }
            else
            {
                authKey = Request.Headers["X-ISA-Auth-Key"];
            }

            //string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];
            SqlConnection myConn = new SqlConnection(connStr);
            myConn.Open();

            string query = "SELECT Metadata FROM Client_Metadata";
            SqlCommand queryCommand = new SqlCommand(query, myConn);
            SqlDataReader queryCommandReader = queryCommand.ExecuteReader();
            XmlDocument clientMetadataXml = new XmlDocument();
            XmlDocument clientListXml = new XmlDocument();

            string groupID = getGroupID(authKey);
            string group = getGroup(groupID);
            string[] sbInfo = getSbInfo();

            XmlDeclaration dec = clientListXml.CreateXmlDeclaration("1.0", null, null);
            clientListXml.AppendChild(dec);

            XmlElement root = clientListXml.CreateElement("iLabClients");
            XmlElement Agent_Name = clientListXml.CreateElement("Agent_Name");
            XmlElement Location = clientListXml.CreateElement("Location");
            XmlElement Agent_GUID = clientListXml.CreateElement("Agent_GUID");
            XmlElement WebService_URL = clientListXml.CreateElement("WebService_URL");
            XmlElement Codebase_URL = clientListXml.CreateElement("Codebase_URL");
            XmlElement groupName = clientListXml.CreateElement("groupName");

            if (group != "-1")
            {
                Agent_Name.InnerText = sbInfo[2];
                Location.InnerText = sbInfo[4];
                Agent_GUID.InnerText = sbInfo[0];
                WebService_URL.InnerText = sbInfo[1];
                Codebase_URL.InnerText = sbInfo[5];
                groupName.InnerText = group;

                root.AppendChild(Agent_Name);
                root.AppendChild(Location);
                root.AppendChild(Agent_GUID);
                root.AppendChild(WebService_URL);
                root.AppendChild(Codebase_URL);
                root.AppendChild(groupName);

                while (queryCommandReader.Read())
                {
                    clientMetadataXml.LoadXml(queryCommandReader["Metadata"].ToString());
                    XmlNode node = clientMetadataXml.SelectSingleNode("/iLabClientMetadata");

                    if (node["groupName"].InnerText == group)
                    {
                        XmlElement iLabClient = clientListXml.CreateElement("iLabClient");
                        string[] clientInfo = getClientInfo(node["clientGuid"].InnerText);

                        XmlElement clientName = clientListXml.CreateElement("clientName");
                        XmlElement duration = clientListXml.CreateElement("duration");
                        XmlElement authCouponId = clientListXml.CreateElement("authCouponId");
                        XmlElement authPasskey = clientListXml.CreateElement("authPasskey");
                        XmlElement clientGuid = clientListXml.CreateElement("clientGuid");
                        XmlElement description = clientListXml.CreateElement("description");

                        clientName.InnerText = clientInfo[0];
                        duration.InnerText = "-1";
                        authCouponId.InnerText = node["authCouponId"].InnerText;
                        authPasskey.InnerText = node["authPasskey"].InnerText;
                        clientGuid.InnerText = clientInfo[1];
                        description.InnerText = clientInfo[2];

                        iLabClient.AppendChild(clientName);
                        iLabClient.AppendChild(duration);
                        iLabClient.AppendChild(authCouponId);
                        iLabClient.AppendChild(authPasskey);
                        iLabClient.AppendChild(clientGuid);
                        iLabClient.AppendChild(description);

                        root.AppendChild(iLabClient);

                    }
                }
            }
            else
            {
                XmlElement errorMessage = clientListXml.CreateElement("errorMessage");
                errorMessage.InnerText = "invalid key";
                root.AppendChild(errorMessage);    
            }

            Response.ContentType = "text/xml";
            myConn.Close();

            clientListXml.AppendChild(root);
            StringWriter sw = new StringWriter();
            XmlTextWriter tx = new XmlTextWriter(sw);
            clientListXml.WriteTo(tx);
            Response.Write(sw.ToString());
            
            Response.Flush();

        }
    }


    private string getGroupID(string authKey)
    { 
        //string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];
        SqlConnection myConn = new SqlConnection(connStr);
        myConn.Open();

        string query = "SELECT Default_Group_ID FROM Authority WHERE Authority_Guid='" + authKey + "'";
        SqlCommand queryCommand = new SqlCommand(query, myConn);
        SqlDataReader reader = queryCommand.ExecuteReader();

            while (reader.Read())
            {
                string result = reader["Default_Group_ID"].ToString();
                reader.Close();
                return result;
            }
            myConn.Close();
            return "-1";

    }

    private string getGroup(string groupID)
    {
        //string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];
        SqlConnection myConn = new SqlConnection(connStr);
        myConn.Open();

        //string query = "SELECT * FROM Client_Metadata";
        string query = "SELECT Group_Name FROM Groups WHERE Group_ID='" + groupID + "'";
        SqlCommand queryCommand = new SqlCommand(query, myConn);
        SqlDataReader reader = queryCommand.ExecuteReader();

        while (reader.Read())
        {
            string result = reader["Group_Name"].ToString();
            //Response.Write(result);

            reader.Close();
            myConn.Close();
            return result;
        }
        myConn.Close();
        return "-1";

    }

    private string[] getSbInfo()
    {
        //string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];
        SqlConnection myConn = new SqlConnection(connStr);
        string[] result = new string[6];
        myConn.Open();

        //string query = "SELECT * FROM Client_Metadata";
        string query = "SELECT Agent_GUID, WebService_URL, Agent_Name, Contact_Email, Location, Codebase_URL FROM ProcessAgent WHERE Self='1'";
        SqlCommand queryCommand = new SqlCommand(query, myConn);
        SqlDataReader reader = queryCommand.ExecuteReader();

        while (reader.Read())
        {
            result[0] = reader["Agent_GUID"].ToString();
            result[1] = reader["WebService_URL"].ToString();
            result[2] = reader["Agent_Name"].ToString();
            result[3] = reader["Contact_Email"].ToString();
            result[4] = reader["Location"].ToString();
            result[5] = reader["Codebase_URL"].ToString();

            reader.Close();
            myConn.Close();
            return result;
        }
        myConn.Close();
        result[0] = "-1";
        return result;

    }

    private string[] getClientInfo(string client_guid)
    {
        //string connStr = System.Configuration.ConfigurationManager.AppSettings["sqlConnection"];
        SqlConnection myConn = new SqlConnection(connStr);
        string[] result = new string[3];
        myConn.Open();

        //string query = "SELECT * FROM Client_Metadata";
        string query = "SELECT Lab_Client_Name, Client_Guid, Long_Description FROM Lab_Clients WHERE Client_Guid='" + client_guid + "'";

        SqlCommand queryCommand = new SqlCommand(query, myConn);
        SqlDataReader reader = queryCommand.ExecuteReader();

        while (reader.Read())
        {
            result[0] = reader["Lab_Client_Name"].ToString();
            result[1] = reader["Client_Guid"].ToString();
            result[2] = reader["Long_Description"].ToString();

            //Response.Write(result);

            reader.Close();
            myConn.Close();
            return result;
        }
        myConn.Close();
        result[0] = "-1";
        return result;

    }


}