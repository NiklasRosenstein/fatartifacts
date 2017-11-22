import React from 'react'
import ReactDOM from 'react-dom'
import $ from 'jquery'


class TableRoot extends React.Component {
  render() {
    return <table className="ui celled table">
      <thead><tr>
        <th>Location</th>
        <th>Date Created</th>
        <th>Date Updated</th>
      </tr></thead>
      <tbody>
        {this.props.children}
      </tbody>
    </table>
  }
}

class TableNamespaceRow extends React.Component {
  constructor(props) {
    super(props)
    let parts = this.props.data.location.split(':')
    let displayName = parts[parts.length-1]
    this.state = {data: props.data, depth: props.depth || 0, displayName: displayName}
    this.toggleOpen = this.toggleOpen.bind(this)
    this.displayMetadata = this.displayMetadata.bind(this)
  }
  getIndentStyle() {
    return {paddingLeft: (this.state.depth-1) * 10 + 'px'}
  }
  render() {
    let result = []
    if (this.state.data.location != '') {  // Don't display the root node.
      result.push(<tr key={this.state.data.location}>
        <td>
          <span style={this.getIndentStyle()}>
            <i className={"angle icon " + (this.state.data.opened ? "down" : "right")}
                onClick={this.toggleOpen} style={{cursor: "pointer"}}/>
            {this.state.displayName}
          </span>
          <i className="icon info" style={{float: "right"}} onClick={this.displayMetadata}/>
        </td>
        <td>{this.state.data.dateCreated}</td>
        <td>{this.state.data.dateUpdated}</td>
      </tr>)
    }
    if (this.state.data.location == '' || (this.state.data.opened && this.state.data.children)) {
      result = result.concat(this.state.data.children.map(item => {
        return <TableNamespaceRow key={item.location} depth={this.state.depth+1} data={item}/>
      }))
    }
    else if (this.state.data.opened && this.state.data.objects) {
      result = result.concat(this.state.data.objects.map(item => {
        return <TableObjectRow key={item.location} depth={this.state.depth+1} data={item}/>
      }))
    }
    return result
  }
  toggleOpen() {
    if (this.state.data.children === undefined && this.state.data.objects === undefined) {
      // Fetch the information from the REST-Api.
      $.ajax('/api/location/' + this.state.data.location, {
        complete: (request, status) => {
          let data = request.responseJSON.location
          this.setState(state => {
            state.data.children = data.children
            state.data.objects = data.objects
            state.data.opened = !state.data.opened
            return state
          })
        }
      })
    }
    else {
      this.setState(state => {
        state.data.opened = !state.data.opened
        return state
      })
    }
  }
  displayMetadata(ev) {
    alert(this.state.data.metadata)
    return true
  }
}

class TableObjectRow extends TableNamespaceRow {
  constructor(props) {
    super(props);
    this.downloadObject = this.downloadObject.bind(this)
  }
  render() {
    return <tr>
      <td>
        <span style={this.getIndentStyle()}>
          <i className={"angle double right icon"}/>
          {this.state.displayName} ({this.state.data.filename})
        </span>
        <i className="icon info" style={{float: "right"}} onClick={this.displayMetadata}/>
        <i className="icon download" style={{float: "right"}} onClick={this.downloadObject}/>
      </td>
      <td>{this.state.data.dateCreated}</td>
      <td>{this.state.data.dateUpdated}</td>
    </tr>
  }
  onclick() {
  }
  downloadObject() {
    document.location = this.state.data.url
  }
}

class Application extends React.Component {
  constructor(props) {
    super(props)
    this.state = {}
  }
  componentDidMount() {
    $.ajax('/api/location', {
      complete: (request, status) => {
        let data = request.responseJSON.location
        this.setState(state => {
          state.rootData = data
          return state
        })
      }
    })
  }
  render() {
    return <div>
      {this.state.rootData &&
        <TableRoot>
          <TableNamespaceRow key={this.state.rootData.location} data={this.state.rootData}/>
        </TableRoot>
      }
    </div>
  }
}


ReactDOM.render(
 <Application/>,
  document.getElementById('container')
)